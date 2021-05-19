import unittest
import numpy as np
import matplotlib.pyplot as plt

from src.application_model.ZirconSeparationUtils import calcEFD, calculateK, GetCoefficients


class MyTestCase(unittest.TestCase):
    '''
    def test_bow(self):
        bow = np.asarray([[0,0],[0,1],[1,1],[1,0],[0.5,0.5]])
        coeffs = calcEFD(bow, len(bow))
        allK, t_radians = calculateK(bow,coeffs)
        print(allK)
        print(t_radians)

        self.assertEqual(len(allK),len(bow))
        self.assertEqual(len(t_radians),len(bow))
        self.assertAlmostEqual(allK[0],allK[3],5)
        self.assertAlmostEqual(allK[1],allK[2],5)
        self.assertGreater (allK[4],0)



    def test_square(self):
        bow = np.asarray([[0,0],[0,1],[1,1],[1,0]])
        coeffs = calcEFD(bow, len(bow))
        allK, t_radians = calculateK(bow,coeffs)
        print(allK)

        self.assertEqual(len(allK),len(bow))
        self.assertEqual(len(t_radians),len(bow))

        self.assertAlmostEqual(allK[1],allK[2],5)
        self.assertAlmostEqual(allK[0],allK[3],5)
        self.assertAlmostEqual(allK[0],allK[1],5)
        self.assertAlmostEqual(allK[2],allK[3],5)'''
    '''

    def test_line(self):
        shape = np.asarray([[0,0], [0.25, 0], [0.5, 0], [0.75, 0], [1,0], [0.5,1]])
        coeffs = calcEFD(shape, len(shape))
        allK, t_radians = calculateK(shape,coeffs)
    '''
    def test_square_with_flat_points(self):
        bow = np.asarray([[0,0],[0,1],[1,1],[1,0],[0.5,0]])
        coeffs,locus, reconstructed_points, keep_contour = GetCoefficients(bow,1)
        x,y = list(zip(*reconstructed_points))

        plt.plot(x,y)
        plt.show()


        #coeffs = calcEFD(bow, len(bow))
        allK, t_radians = calculateK(bow,coeffs)
        print(allK)

        self.assertEqual(len(allK),len(bow))
        self.assertEqual(len(t_radians),len(bow))
        self.assertAlmostEqual(allK[1],allK[2],5)
        self.assertAlmostEqual(allK[0],allK[3],5)
        self.assertAlmostEqual(allK[0],allK[1],5)
        self.assertAlmostEqual(allK[2],allK[3],5)
        self.assertAlmostEqual(allK[4],0,5)


if __name__ == '__main__':
    unittest.main()
