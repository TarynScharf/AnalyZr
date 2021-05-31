import math
import unittest
import numpy as np
import matplotlib.pyplot as plt
import pyefd
from matplotlib.collections import LineCollection

from src.model import ZirconSeparationUtils

class MyTestCase(unittest.TestCase):

    #######################
    ## Utility functions ##
    #######################

    def _create_contour(self, points, noise=0, points_per_line=1):
        np.random.seed(1)

        contour = []
        for i in range(len(points)):
            j = i+1 if i+1 < len(points) else 0
            (x0, y0) = points[i]
            (x1, y1) = points[j]
            xs = np.linspace(x0, x1, points_per_line, endpoint=False) + np.random.normal(0,noise,points_per_line)
            ys = np.linspace(y0, y1, points_per_line, endpoint=False) + np.random.normal(0,noise,points_per_line)
            for x,y in zip(xs,ys):
                contour.append((x,y))

        return np.array(contour)

    def _plot_result(self, contours,breaklines=None):
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        ax1.set_title("Test failure")
        for contour in contours:
            x, y = zip(*contour.reconstructed_points)
            if contour.max_curvature_coordinates:
                end_points = contour.max_curvature_coordinates + np.multiply(contour.max_bisectors,np.array([2,2]))
                bisection_vecors = zip(contour.max_curvature_coordinates,end_points)
                line_collection = LineCollection(bisection_vecors)
                ax1.add_collection(line_collection)
            ax1.plot(*zip(*contour.reconstructed_points))
            ax1.scatter(x, y, c=contour.curvature_values, s=50)
            if contour.max_curvature_coordinates:
                ax1.scatter(*zip(*contour.max_curvature_coordinates), facecolors='none', edgecolors='red', s=345, linewidth=2)
            for i, label in enumerate(contour.curvature_values[:-1]):
                ax1.annotate((i,round(label,2)), (x[i]+0.15, y[i]), fontsize='small')
        if breaklines:
            breakline_collection = LineCollection(breaklines)
            ax1.add_collection(breakline_collection)
        ax1.set_aspect('equal', adjustable='box')

        ax2.set_title("Original contour")

        for contour in contours:
            ax2.plot(*zip(*contour.original_points), marker='o')
        ax2.set_aspect('equal', adjustable='box')

        ax3.set_title("Elliptical reconstruction")
        for contour in contours:
            high_res = pyefd.reconstruct_contour(contour.coefficients, contour.locus, 400)
            ax3.plot(*zip(*high_res))#, marker='o')
        ax3.set_aspect('equal', adjustable='box')
        #ax3.scatter(x, y, c=contour.curvature_values, s=215)

        plt.show(block=True)

    def _calculate_maxima(self, contour):
        return ZirconSeparationUtils.calculate_curvature_and_find_maxima(
            0, contour, np.array([-1, -1, -1, -1]), lambda c: True,True)

    ################
    ## Test cases ##
    ################

    def mtest_irregular(self):
        str = "[[0,0],[0,190],[238,190],[238,189],[239,188],[240,188],[241,187],[239,187],[239,188],[238,189],[237,188],[237,185],[236,185],[235,184],[235,182],[236,181],[235,181],[234,180],[233,180],[232,179],[231,179],[230,178],[229,178],[228,177],[227,177],[226,176],[224,176],[223,175],[213,175],[212,174],[196,174],[195,173],[179,173],[178,172],[178,170],[179,169],[180,169],[189,160],[190,160],[195,155],[195,154],[196,153],[196,147],[197,146],[197,22],[196,21],[196,20],[195,19],[193,19],[192,18],[191,18],[190,17],[184,17],[183,16],[177,16],[176,15],[170,15],[169,16],[168,16],[166,18],[165,18],[164,19],[164,20],[163,21],[163,24],[162,25],[162,40],[161,41],[161,54],[160,55],[160,61],[159,62],[159,79],[158,80],[158,84],[157,85],[157,96],[156,97],[156,164],[157,165],[157,169],[155,171],[142,171],[141,172],[134,172],[133,171],[130,171],[129,170],[121,170],[120,169],[111,169],[110,168],[94,168],[93,167],[84,167],[83,168],[82,167],[82,166],[84,164],[86,164],[88,162],[89,162],[90,161],[91,161],[92,160],[93,160],[94,159],[95,159],[96,158],[97,158],[98,157],[99,157],[100,156],[101,156],[102,155],[103,155],[104,154],[105,154],[106,153],[107,153],[108,152],[109,152],[110,151],[111,151],[113,149],[115,149],[117,147],[119,147],[120,146],[121,146],[122,145],[123,145],[124,144],[125,144],[126,143],[127,143],[128,142],[129,142],[131,140],[132,140],[133,139],[134,139],[137,136],[137,135],[139,133],[139,132],[141,130],[141,129],[144,126],[144,125],[146,123],[146,122],[147,121],[147,120],[148,119],[148,118],[149,117],[149,111],[150,110],[150,102],[149,101],[149,93],[148,92],[148,91],[143,86],[142,86],[140,84],[139,84],[137,82],[136,82],[134,80],[133,80],[131,78],[130,78],[126,74],[125,74],[121,70],[120,70],[119,69],[116,69],[115,68],[104,68],[103,69],[101,69],[100,70],[97,70],[96,71],[95,71],[94,72],[93,72],[92,73],[91,73],[90,74],[89,74],[88,75],[87,75],[86,76],[85,76],[84,77],[83,77],[82,78],[80,78],[79,79],[78,79],[77,80],[76,80],[75,81],[74,81],[73,82],[71,82],[70,83],[69,83],[68,84],[67,84],[66,85],[65,85],[64,86],[63,86],[62,87],[61,87],[60,88],[59,88],[58,89],[57,89],[56,90],[55,90],[54,91],[52,91],[51,92],[50,92],[49,93],[48,93],[47,94],[46,94],[45,95],[44,95],[43,96],[42,96],[41,97],[40,97],[39,98],[38,98],[37,99],[35,99],[34,100],[33,100],[32,101],[31,101],[30,102],[29,101],[29,100],[31,98],[33,98],[35,96],[36,96],[37,95],[38,95],[39,94],[40,94],[41,93],[42,93],[43,92],[44,92],[45,91],[46,91],[48,89],[49,89],[50,88],[51,88],[52,87],[53,87],[54,86],[55,86],[56,85],[57,85],[59,83],[61,83],[62,82],[63,82],[65,80],[66,80],[67,79],[68,79],[70,77],[71,77],[72,76],[73,76],[74,75],[75,75],[76,74],[77,74],[78,73],[79,73],[81,71],[82,71],[83,70],[84,70],[85,69],[86,69],[88,67],[89,67],[90,66],[91,66],[97,60],[97,59],[99,57],[99,55],[100,54],[100,52],[101,51],[101,50],[102,49],[102,47],[103,46],[103,42],[104,41],[104,29],[105,28],[106,28],[108,30],[108,31],[113,36],[113,37],[119,43],[120,43],[125,48],[126,48],[127,49],[128,49],[129,50],[132,50],[133,51],[139,51],[140,50],[146,50],[149,47],[149,46],[150,45],[150,44],[151,43],[151,42],[152,41],[152,40],[153,39],[153,36],[154,35],[154,33],[155,32],[155,31],[156,30],[156,27],[157,26],[157,25],[159,23],[159,22],[160,21],[160,20],[161,19],[161,17],[163,15],[163,13],[164,12],[164,7],[163,6],[163,4],[162,3],[162,0]]"
        contour = np.array(eval(str))

        result = self._calculate_maxima(contour)
        self._plot_result(result)

    def mtest_box(self):
        contour, high_k_indices = self._create_contour([
            ((0, 0)),
            ((0, 10)),
            ((5, 5.2)),
            ((10, 10)),
            ((15, 5.2)),
            ((20, 10)),
            ((25, 5.2)),
            ((30, 10)),
            ((30, 0)),
            ((25, 4.8)),
            ((20, 0)),
            ((15, 4.8)),
            ((10, 0)),
            ((5, 4.8)),
        ], noise=0.0)

        result = self._calculate_maxima(contour)
        self._plot_result(result)

    def test_angles(self):
        contour = self._create_contour([
            (0,0),
            (30,0),
            (30,10),
            (25,15),
            (30,20),
            (30,30),
            (23,30),
            (22,25),
            (21,30),
            (0,30),
            (0,20),
            (5,15),
            (0,10)
        ], points_per_line=5)
        contour = np.flip(contour, axis=0)

        composite_contour = self._calculate_maxima(contour)
        node_pairs = ZirconSeparationUtils.process_contour_group_for_node_pairs([composite_contour])
        assert len(node_pairs)==1
        self.assert_breakline_equals(node_pairs[0],(5,15),(25,15))

        #self._plot_result(composite_contour,node_pairs)

    def test_parent_child_links(self):
        parent_contour = self._create_contour([
            (0, 0),
            (30, 0),
            (25, 10),
            (30, 20),
            (0, 20),
            (5, 10),

        ], points_per_line=5)
        parent_contour=np.flip(parent_contour, axis=0)

        child_contour = self._create_contour([
            (10, 10),
            (15, 5),
            (20, 10),
            (15, 15),

        ], points_per_line=5)
        #child_contour=np.flip(child_contour, axis=0)

        parent_composite_contour = self._calculate_maxima(parent_contour)
        child_composite_contour = self._calculate_maxima(child_contour)

        contour_group=[parent_composite_contour,child_composite_contour]

        node_pairs = ZirconSeparationUtils.process_contour_group_for_node_pairs(contour_group)
        self._plot_result(contour_group, node_pairs)
        assert len(node_pairs) == 2
        self.assert_breakline_equals(node_pairs[0],(10,10),(15,10))
        self.assert_breakline_equals(node_pairs[1], (10, 0), (15, 10))



    def assert_breakline_equals(self,node_pair,p1,p2):
        (x1, y1), (x2, y2) = node_pair
        assert math.isclose(x1, p1[0], abs_tol=1)
        assert math.isclose(y1, p1[1], abs_tol=1)
        assert math.isclose(x2, p2[0], abs_tol=1)
        assert math.isclose(y2, p2[1], abs_tol=1)



if __name__ == '__main__':
    unittest.main()
