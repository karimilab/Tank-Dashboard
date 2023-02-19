import numpy as np
from molecules.Component import Component

class Nitrogen(Component):
    def vapor_pressure(T):
        P_s = 0.014*(T**3) - 2.8301*(T**2) + 199.4*T - 4876.1
        return P_s
    
    def density(T):
        LD = 669.8 + 0*T
        return LD
    
    def liq_enthalpy(T):
        x = np.array(T)

        Tmin = -170 + 273.15
        Tmax = -130 + 273.15
        x = (x - Tmin) / (Tmax - Tmin)

        Q = x.shape[0]

        x_xoffset = 0.05
        x_gain = 4
        x_ymin = -1

        # Layer 1
        b1 = [[-15.516368112694996384],[-4.7333018385960725638],[5.4230207178790754696],[-1.8121302102701355441],[0.79202507019238332919],
            [-0.33609945719694622746],[-0.70998805367653761156],[-3.1526052188641000562],[3.9870958674134833188],[0.19790035328479724241]]
        b1 = np.array(b1)

        IW1_1 = [[14.060969148565257925],[4.2056557613797815876],[-6.4299593833526964559],[2.3222925917950134611],[-2.8893521120155232218],
                [6.6770298891771666661],[-4.2415910552605859962],[-7.8259598007806063791],[6.8140436912195285757],[0.39944259965013573233]]
        IW1_1 = np.array(IW1_1)

        # Layer 2
        b2 = [[0.10399347896290118964], [6.0578349507971562815]]
        b2 = np.array(b2)

        LW2_1 = [[0.12356776836412250442, 0.32692780524792180996, -0.0016836700563337832996, 0.22181813988853746333, -0.041446288678668154193,
                0.0024006092288715390713, -0.010887020065948478306, -0.0014395719810286939939, 0.0011830403102223235271, 1.8747749546492022965],
                [4.7312425382594858192, 2.0801345155203190274, 0.049836892190000418867, 0.22373788020891205441, -0.030037016091673477552,
                0.0012667416975219063843, -0.0086101422314055851143, -0.0013799189264877204705, 0.0018452364993540798857, 0.14998667672877841195]]
        LW2_1 = np.array(LW2_1)

        # Output 1
        y1_ymin = -1
        y1_gain = [[2.92696956351691*10**(-5)], [0.000130912494070219]]
        y1_xoffset = [[4865.898457409], [2483.46071915761]]

        xp1 = [(x[i][0] - x_xoffset) * x_gain + x_ymin for i in range(len(x))]

        a1 = np.empty((len(b1), 0))
        a2 = np.array([])

        for i in range(len(xp1)):
            b3 = b1 + IW1_1*xp1[i]
            a = 2 / (1 + np.exp(-2*b3)) - 1
            a1 = np.append(a1, a, axis=1)

        a2 = np.repeat(b2, Q, axis=1) + np.matmul(LW2_1, a1)

        a3 = a2 - y1_ymin
        a3 = np.divide(a3, y1_gain)
        a3 = a3 + y1_xoffset

        y1 = np.transpose(a3)

        return y1[:,0]
    
    def vap_enthalpy(T):
        x = np.array(T)

        Tmin = -170 + 273.15
        Tmax = -130 + 273.15
        x = (x - Tmin) / (Tmax - Tmin)

        Q = x.shape[0]

        x_xoffset = 0.05
        x_gain = 4
        x_ymin = -1

        # Layer 1
        b1 = [[-16.728889076209817688],[7.2885377777552253775],[2.8955273516714989945],[-4.8986068299936826875],[0.9103546724176426741],
            [-0.85130356229898440645],[2.0104980739694942038],[-4.7885374676421923468],[3.2623031179543064972],[11.472224167182426768]]
        b1 = np.array(b1)

        IW1_1 = [[15.20608017808306478],[-6.942547148515754607],[-2.7360303596125974401],[8.6245444332771832308],[-0.87826665584290253275],
                [-7.9291034051421194206],[5.6244995277031817338],[-8.0227675591217249007],[4.0510652916412208668],[11.965922634099300126]]
        IW1_1 = np.array(IW1_1)

        # Layer 2
        b2 = [[-1.5142907437795793957], [5.5526680938235344343]]
        b2 = np.array(b2)

        LW2_1 = [[-0.34237453705637554968, 0.2242164355824160793, 0.51716082108485683655, -0.00021749339754577600185, 1.5095390219669932996,
                0.00079578599849310972542, -0.0025626485598984473195, 0.0011235902871381253914, 0.0011309309018020200378, 0.0016395515476868025365],
                [4.5090688235896569935, -1.0065621606839696422, -0.70003276269518777131, -0.0013223457513428236217, -0.35541177300232057457,
                0.00015068729005880863937, 0.00033673208018149546365, -0.00025495552796281692595, 0.0023571620852443943284, 0.00053872675420535128064]]
        LW2_1 = np.array(LW2_1)

        # Output 1
        y1_ymin = -1
        y1_gain = [[5.97307921400538*10**(-5)], [8.34892291973195*10**(-5)]]
        y1_xoffset = [[119798.414603824], [1752.32295685507]]

        xp1 = [(x[i][0] - x_xoffset) * x_gain + x_ymin for i in range(len(x))]

        a1 = np.empty((len(b1), 0))
        a2 = np.array([])


        for i in range(len(xp1)):
            b3 = b1 + IW1_1*xp1[i]
            a = 2 / (1 + np.exp(-2*b3)) - 1
            a1 = np.append(a1, a, axis=1)

        a2 = np.repeat(b2, Q, axis=1) + np.matmul(LW2_1, a1)

        a3 = a2 - y1_ymin
        a3 = np.divide(a3, y1_gain)
        a3 = a3 + y1_xoffset

        y1 = np.transpose(a3)

        return y1[:,0]

    def liq_heat_capacity(T):
        x = np.array(T)

        Tmin = -170 + 273.15
        Tmax = -130 + 273.15
        x = (x - Tmin) / (Tmax - Tmin)

        Q = x.shape[0]

        x_xoffset = 0.05
        x_gain = 4
        x_ymin = -1

        # Layer 1
        b1 = [[-15.516368112694996384],[-4.7333018385960725638],[5.4230207178790754696],[-1.8121302102701355441],[0.79202507019238332919],
            [-0.33609945719694622746],[-0.70998805367653761156],[-3.1526052188641000562],[3.9870958674134833188],[0.19790035328479724241]]
        b1 = np.array(b1)

        IW1_1 = [[14.060969148565257925],[4.2056557613797815876],[-6.4299593833526964559],[2.3222925917950134611],[-2.8893521120155232218],
                [6.6770298891771666661],[-4.2415910552605859962],[-7.8259598007806063791],[6.8140436912195285757],[0.39944259965013573233]]
        IW1_1 = np.array(IW1_1)

        # Layer 2
        b2 = [[0.10399347896290118964], [6.0578349507971562815]]
        b2 = np.array(b2)

        LW2_1 = [[0.12356776836412250442, 0.32692780524792180996, -0.0016836700563337832996, 0.22181813988853746333, -0.041446288678668154193,
                0.0024006092288715390713, -0.010887020065948478306, -0.0014395719810286939939, 0.0011830403102223235271, 1.8747749546492022965],
                [4.7312425382594858192, 2.0801345155203190274, 0.049836892190000418867, 0.22373788020891205441, -0.030037016091673477552,
                0.0012667416975219063843, -0.0086101422314055851143, -0.0013799189264877204705, 0.0018452364993540798857, 0.14998667672877841195]]
        LW2_1 = np.array(LW2_1)

        # Output 1
        y1_ymin = -1
        y1_gain = [[2.92696956351691*10**(-5)], [0.000130912494070219]]
        y1_xoffset = [[4865.898457409], [2483.46071915761]]

        xp1 = [(x[i][0] - x_xoffset) * x_gain + x_ymin for i in range(len(x))]

        a1 = np.empty((len(b1), 0))
        a2 = np.array([])

        for i in range(len(xp1)):
            b3 = b1 + IW1_1*xp1[i]
            a = 2 / (1 + np.exp(-2*b3)) - 1
            a1 = np.append(a1, a, axis=1)

        a2 = np.repeat(b2, Q, axis=1) + np.matmul(LW2_1, a1)

        a3 = a2 - y1_ymin
        a3 = np.divide(a3, y1_gain)
        a3 = a3 + y1_xoffset

        y1 = np.transpose(a3)

        return y1[:,1]


    def vap_heat_capacity(T):
        x = np.array(T)

        Tmin = -170 + 273.15
        Tmax = -130 + 273.15
        x = (x - Tmin) / (Tmax - Tmin)

        Q = x.shape[0]

        x_xoffset = 0.05
        x_gain = 4
        x_ymin = -1

        # Layer 1
        b1 = [[-16.728889076209817688],[7.2885377777552253775],[2.8955273516714989945],[-4.8986068299936826875],[0.9103546724176426741],
            [-0.85130356229898440645],[2.0104980739694942038],[-4.7885374676421923468],[3.2623031179543064972],[11.472224167182426768]]
        b1 = np.array(b1)

        IW1_1 = [[15.20608017808306478],[-6.942547148515754607],[-2.7360303596125974401],[8.6245444332771832308],[-0.87826665584290253275],
                [-7.9291034051421194206],[5.6244995277031817338],[-8.0227675591217249007],[4.0510652916412208668],[11.965922634099300126]]
        IW1_1 = np.array(IW1_1)

        # Layer 2
        b2 = [[-1.5142907437795793957], [5.5526680938235344343]]
        b2 = np.array(b2)

        LW2_1 = [[-0.34237453705637554968, 0.2242164355824160793, 0.51716082108485683655, -0.00021749339754577600185, 1.5095390219669932996,
                0.00079578599849310972542, -0.0025626485598984473195, 0.0011235902871381253914, 0.0011309309018020200378, 0.0016395515476868025365],
                [4.5090688235896569935, -1.0065621606839696422, -0.70003276269518777131, -0.0013223457513428236217, -0.35541177300232057457,
                0.00015068729005880863937, 0.00033673208018149546365, -0.00025495552796281692595, 0.0023571620852443943284, 0.00053872675420535128064]]
        LW2_1 = np.array(LW2_1)

        # Output 1
        y1_ymin = -1
        y1_gain = [[5.97307921400538*10**(-5)], [8.34892291973195*10**(-5)]]
        y1_xoffset = [[119798.414603824], [1752.32295685507]]

        xp1 = [(x[i][0] - x_xoffset) * x_gain + x_ymin for i in range(len(x))]

        a1 = np.empty((len(b1), 0))
        a2 = np.array([])


        for i in range(len(xp1)):
            b3 = b1 + IW1_1*xp1[i]
            a = 2 / (1 + np.exp(-2*b3)) - 1
            a1 = np.append(a1, a, axis=1)

        a2 = np.repeat(b2, Q, axis=1) + np.matmul(LW2_1, a1)

        a3 = a2 - y1_ymin
        a3 = np.divide(a3, y1_gain)
        a3 = a3 + y1_xoffset

        y1 = np.transpose(a3)

        return y1[:,1]