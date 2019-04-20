import networkx as nx
import numpy as np
import pygsp
from tqdm import tqdm

class GraphWave:

    def __init__(self, graph, settings):

        self.settings = settings
        self.graph = graph
        self.n_nodes = nx.number_of_nodes(graph)
        self.nodes = list(nx.nodes(graph))

        self.G = pygsp.graphs.Graph(nx.adjacency_matrix(graph))
        self.G.compute_fourier_basis()

        self.eigenvectors = self.G.U
        self.eigenvalues = self.G.e

        self.sample_points = list(map(lambda x: x * self.settings.step_size, range(0, self.settings.sample_number)))


    def _exact_embedding(self):
        pass

    def _approx_embedding(self, mode="cha"):
        """
        Given the Chebyshev polynomial, graph the approximate embedding is calculated.
        """
        self.G.estimate_lmax()
        self.heat_filter = pygsp.filters.Heat(self.G, tau=[self.settings.heat_coefficient])
        self.chebyshev = pygsp.filters.approximations.compute_cheby_coeff(self.heat_filter, m=self.settings.approximation)

        self.embeddings = dict()
        for node_idx in tqdm(range(self.n_nodes)):
            impulse = np.zeros((self.n_nodes))
            impulse[node_idx] = 1
            wavelet_coefficietns = pygsp.filters.approximations.cheby_op(self.G, self.chebyshev, impulse)
            self.embeddings[self.nodes[node_idx]] = self._cal_embedding(wavelet_coefficietns, mode)
        return self.embeddings


    def _check_node(self, node_idx):
        if node_idx < 0 or node_idx > self.n_nodes:
            raise ValueError("node_idx is not valid: node_idx{}".format(node_idx))


    def _check_wavelet_coefficients(self, coefficients):
        if len(coefficients) != self.n_nodes:
            raise TypeError("The number of coefficients should be {}, error:{}".format(self.n_nodes, len(coefficients)))


    def _calculate_node_coefficients(self, node_idx, scale):
        impulse = np.zeros(shape=(self.n_nodes))
        impulse[node_idx] = 1
        coefficients = np.dot(np.dot(np.dot(self.eigenvectors, np.diag(np.exp(-scale * self.eigenvalues))),
                             np.transpose(self.eigenvectors)), impulse)
        return coefficients


    def _cal_embedding(self, wavelet_coefficients, mode="cha"):
        """
        用小波系数去计算嵌入。
        :param wavelet_coefficients:
        :param sample_points:
        :param mode:
        :return:
        """
        if mode not in ["cha", "mog", "mo"]:
            raise ValueError("The embedding mode:{} is not supported.".format(mode))
        embedding = []
        for t in self.sample_points:
            if mode == "cha":
                value = np.mean(np.exp(1j * wavelet_coefficients * t))
                embedding.append(value.real)
                embedding.append(value.imag)
            elif mode == "mog":
                value = np.mean(np.exp(wavelet_coefficients * t))
                embedding.append(value)
            elif mode == "mo":
                value = np.mean(wavelet_coefficients ** t)
                embedding.append(value)
        return embedding


    def single_scale_embedding(self, heat_coefficient, mode="cha"):
        """
        :param heat_coefficient:  parameter scale.
        :param mode: characteristic function, moment generating function, moment
        :return:
        """

        if mode not in ["cha", "mog", "mo"]:
            raise ValueError("The embedding mode:{} is not supported.".format(mode))

        sample_points = list(map(lambda x: x * self.settings.step_size, range(0, self.settings.sample_number)))
        self.embeddings = dict()
        for node_idx in tqdm(range(self.n_nodes)):
            node_coeff = self._calculate_node_coefficients(node_idx, heat_coefficient)
            embedding = []
            for t in sample_points:
                if mode == "cha":
                    value = np.mean(np.exp(1j * node_coeff * t))
                    embedding.append(value.real)
                    embedding.append(value.imag)
                elif mode == "mog":
                    value = np.mean(np.exp(node_coeff * t))
                    embedding.append(value)
                elif mode == "mo":
                    value = np.mean(node_coeff ** t)
                    embedding.append(value)
            self.embeddings[self.nodes[node_idx]] = np.array(embedding)
        return self.embeddings


    def multi_scale_embedding(self, scales, mode="cha"):
        """
        多尺度嵌入
        :param scales: [scale_1, scale_2, ...]
        :param mode:  embedding mode.
        :return:
        """

        if mode not in ["cha", "mog", "mo"]:
            raise ValueError("The embedding mode:{} is not supported.".format(mode))

        multi_embeddings = dict()
        for i in tqdm(range(len(scales))):
            multi_embeddings[scales[i]] = self.single_scale_embedding(scales[i], mode)
        return multi_embeddings


    def _dev_coeff_research(self, scale):
        """
        The method is used to analyse wavelet coefficients.
        :param scale: parameter : heat coefficient
        :return:
        """

        coeffs = []
        for node_idx in range(self.n_nodes):
            _coeff = self._calculate_node_coefficients(node_idx, scale)
            coeffs.append(_coeff)
        path_len_coeffs = dict()
        for node_idx1 in range(self.n_nodes):
            for node_idx2 in range(self.n_nodes):
                shortest_path_len = nx.dijkstra_path_length(self.graph, self.n_nodes[node_idx1], self.n_nodes[node_idx2])
                path_len_coeffs[shortest_path_len] = path_len_coeffs.get(shortest_path_len, []) + [coeffs[node_idx1][node_idx2]]
        path_average_coeff = dict()
        for _len, _coeffs in path_len_coeffs.items():
            path_average_coeff[_len] = np.mean(np.array(_coeffs))

        return path_average_coeff, path_average_coeff










