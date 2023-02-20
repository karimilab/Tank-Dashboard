import math
import pandas as pd
import numpy as np
from scipy.stats import poisson
import importlib
from assimulo.problem import Implicit_Problem
from assimulo.solvers import IDA
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from io import BytesIO

ModelF = importlib.import_module(f"neuralNetwork.ModelF")
ModelZg = importlib.import_module(f"neuralNetwork.ModelZg")

class Tank:
    def __init__(self, noFeedStreams, noProductStreams, tankDiameter, tankHeight, initialPressure, 
            initialLiquidHeight, feeds, products, feed_product_df,
            noComponents, molecular_weights, componentList,  
            jacketStartValue, jacketEndValue, sigma, Ul,
            Uv, Uvw, Ulw, Ur, Ub, Uvr, Ulr, groundTemp, ambTemp, roofTemp, refridgeTemp, 
            noLDisks, noVDisks, abstol, reltol, numberofIterations, diskinitCombined):
        self.noFeedStreams = noFeedStreams
        self.noProductStreams = noProductStreams
        self.tankDiameter = tankDiameter  ## Tank Diameter (m)
        self.tankHeight = tankHeight  ## Tank Height (m)
        self.initialPressure = initialPressure
        self.initialLiquidHeight = initialLiquidHeight
        self.tankArea = 0.25 * math.pi * (self.tankDiameter ** 2)
        self.feeds = feeds
        self.products = products
        self.feed_product_df = feed_product_df
        self.noComponents = noComponents
        self.molecular_weights = molecular_weights
        self.componentList = componentList
        self.jacketStartValue = jacketStartValue
        self.jacketEndValue = jacketEndValue
        self.sigma = sigma
        self.Ul = Ul
        self.Uv = Uv
        self.Uvw = Uvw
        self.Ulw = Ulw
        self.Ur = Ur
        self.Ub = Ub
        self.Uvr = Uvr
        self.Ulr = Ulr
        self.groundTemp = groundTemp
        self.ambTemp = ambTemp
        self.roofTemp = roofTemp
        self.refridgeTemp = refridgeTemp
        self.noLDisks = noLDisks
        self.noVDisks = noVDisks
        self.abstol = abstol
        self.reltol = reltol
        self.numberofIterations = numberofIterations
        self.diskinitCombined = diskinitCombined

    def check_input(self):
        for i in range(1,self.noComponents+1):
            if self.molecular_weights[i] == 0.0:
                return f'Molecular weight for component {i} is empty.'
        if self.jacketStartValue > self.jacketEndValue:
            return "Value of jacket start point is greater than the value of jacket end point."
        if self.numberofIterations % 5 != 0:
            return "Running time is not a positive integer divisible by 5."
        for i in range(self.noProductStreams):
            df = self.feed_product_df[f"Product {i+1}"]
            if df.empty or df.isna().values.any():
                return f"Missing values in Product {i+1} data"
        for i in range(self.noFeedStreams):
            df = self.feed_product_df[f"Feed {i+1}"]
            if df.empty or df.isna().values.any():
                return f"Missing values in Feed {i+1} data"
        if self.diskinitCombined.empty or self.diskinitCombined.isna().values.any():
            return f"Missing values in Disk Initial Conditions"
        for _, row in self.diskinitCombined.iterrows():
            diskName = row["Disk Number"]
            components = [f"Component {i}" for i in range(1,self.noComponents+1)]
            if sum(row[components]) != 1.0:
                return f"Composition summation for {diskName} is not equal to 1 in Disk Initial Conidtions"
        return True

    def data_preprocessing(self):
        Ag_keys = [f'Ag({i+1})' for i in range(self.noProductStreams)]
        self.Ag_dict = dict.fromkeys(Ag_keys, 0)

        for j in range(self.noProductStreams):
            df = self.feed_product_df[f"Product {j+1}"]
            time_len = int(df.iloc[-1, 0] / 5) + 1
            time = [5 * i for i in range(time_len)]
            Ag_list = [None] * len(time)
            Bg_list = [0] * len(time)
            for i in range(len(time)):
                if time[i] in df.iloc[:, 0].values:
                    Ag_list[i] = df[df.iloc[:, 0] == time[i]].iloc[:, 1].values.tolist()[0]
                else:
                    k = i
                    while time[k] not in df.iloc[:, 0].values:
                        k = k - 1
                    Ag_list[i] = Ag_list[k]

            for i in range(len(Ag_list) - 1):
                if Ag_list[i] != Ag_list[i + 1]:
                    Bg_list[i] = (Ag_list[i + 1] - Ag_list[i]) / (5 * 60)
                else:
                    pass
            Ag_df = pd.DataFrame([time, Ag_list, Bg_list]).T
            Ag_df.columns = ['Time(min)', 'Ag({})'.format(j + 1), 'Bg({})'.format(j + 1)]
            self.Ag_dict[Ag_keys[j]] = Ag_df

        # Pre-processing Af(1)
        noFeedStream = self.noFeedStreams

        Af_keys = ['Af({})'.format(str(i + 1)) for i in range(noFeedStream)]
        AZ_keys = ['AZ({})'.format(str(i + 1)) for i in range(noFeedStream)]
        BZ_keys = ['BZ({})'.format(str(i + 1)) for i in range(noFeedStream)]
        self.Af_dict = dict.fromkeys(Af_keys, 0)
        self.AZ_dict = dict.fromkeys(AZ_keys, 0)
        self.BZ_dict = dict.fromkeys(BZ_keys, 0)

        for j in range(noFeedStream):
            df = self.feed_product_df[f"Feed {j+1}"]
            time_len = int(df.iloc[-1, 0] / 5) + 1
            time = [5 * i for i in range(time_len)]
            Af_list = [None] * len(time)
            ATf_list = [None] * len(time)
            APf_list = [None] * len(time)
            componentName = ['Z{}'.format(str(i + 1)) for i in range(self.noComponents)]
            AZ_dict = dict.fromkeys(componentName, 0)
            for key in AZ_dict:
                AZ_dict[key] = ['None'] * len(time)

            for i in range(len(time)):
                if time[i] in df.iloc[:, 0].values:
                    Af_list[i] = df[df.iloc[:, 0] == time[i]].iloc[:, 1].values.tolist()[0]
                    ATf_list[i] = df[df.iloc[:, 0] == time[i]].iloc[:, 2].values.tolist()[0]
                    APf_list[i] = df[df.iloc[:, 0] == time[i]].iloc[:, 3].values.tolist()[0]
                    for comp in range(1,self.noComponents+1):  # Z1, Z2, Z3,...
                        AZ_dict[f"Z{comp}"][i] = df[df.iloc[:, 0] == time[i]][f"Mass Frac {comp}"].values.tolist()[0]
                else:
                    k = i
                    while time[k] not in df.iloc[:, 0].values:
                        k = k - 1
                    Af_list[i] = Af_list[k]
                    ATf_list[i] = ATf_list[k]
                    APf_list[i] = APf_list[k]
                    for key in AZ_dict:
                        AZ_dict[key][i] = AZ_dict[key][k]

            Bf_list = [0] * len(time)
            BTf_list = [0] * len(time)
            BPf_list = [0] * len(time)

            BZ_dict = dict.fromkeys(componentName, 0)

            for key in BZ_dict:
                BZ_dict[key] = [0] * len(time)
            for i in range(len(Af_list) - 1):
                if Af_list[i] != Af_list[i + 1]:
                    Bf_list[i] = (Af_list[i + 1] - Af_list[i]) / (5 * 60)
                if ATf_list[i] != ATf_list[i + 1]:
                    BTf_list[i] = (ATf_list[i + 1] - ATf_list[i]) / 5
                if APf_list[i] != APf_list[i + 1]:
                    BPf_list[i] = (APf_list[i + 1] - APf_list[i]) / 5

                for key in BZ_dict:
                    if AZ_dict[key][i] != AZ_dict[key][i + 1]:
                        BZ_dict[key][i] = (AZ_dict[key][i + 1] - AZ_dict[key][i]) / 5

            Af_df = pd.DataFrame([time, Af_list, Bf_list, ATf_list, BTf_list, APf_list, BPf_list])
            Af_df = Af_df.T
            Af_df.columns = ['Time(min)', 'Af({})'.format(str(j + 1)), 'Bf({})'.format(str(j + 1)),
                             'ATf({})'.format(str(j + 1)),
                             'BTf({})'.format(str(j + 1)), 'APf({})'.format(str(j + 1)), 'BPf({})'.format(str(j + 1))]
            self.Af_dict[Af_keys[j]] = Af_df

            AZ_df_list = [AZ_dict[key] for key in AZ_dict]
            AZ_df = pd.DataFrame(AZ_df_list).T
            AZ_df.columns = componentName
            self.AZ_dict[AZ_keys[j]] = AZ_df

            BZ_df_list = [BZ_dict[key] for key in BZ_dict]
            BZ_df = pd.DataFrame(BZ_df_list).T
            BZ_df.columns = componentName
            self.BZ_dict[BZ_keys[j]] = BZ_df
    
    def run_simulation(self):
        I = self.noComponents

        ## Fluid Properties and Constants
        g = 9.81  ## gravitational acceleration (m2/s)
        R = 8.314  ## gas constant
        # Z = float(self.compressFactortext.text())  # Compressibility Factor

        ## Fixed DAE model parameters, scale factors, and reference
        N = self.noLDisks + self.noVDisks
        F = self.noFeedStreams
        S = self.noProductStreams
        Tref = 100  # Scale factor for temperature
        LDref = 400  # Reference liquid density (kg/m3)
        VDref = 2  # Reference vapor density (kg/m3)
        A = self.tankArea
        H = self.tankHeight
        D = self.tankDiameter
        Lref = A * H * LDref / N
        Vref = A * H * VDref / N
        NL = self.noLDisks
        NV = N - NL  # number of vapor disks
        NC = N + N * I
        NE = NC + N - 2
        sigma = self.sigma * 1000  # evaporation model coefficient (2E-5,5E-5,1E-4)

        MW = [self.molecular_weights[x] for x in range(1,self.noComponents+1)]  # component molecular weights (kg/kmol)
        nf = [self.feeds[x] * H/100 for x in range(1,self.noFeedStreams+1)]
        ng = [self.products[x] * H/100 for x in range(1,self.noProductStreams+1)]

        ## Temperatures, heat transfer coefficients, and other parameters
        # global Tamb, Tb, Tj, Tr, Ul, Uv, Ur, Ui, Uvw, Ulw, Ub, Uvr, Ulr, nJ
        Tb = self.groundTemp  # Ground temperature (K)
        Tamb = [self.ambTemp, 0, 0]  # ambient temperature as a function of t (K)
        Tr = self.roofTemp  # roof temperature (K)
        Ul = self.Ul  # liquid phase film heat transfer coefficient (W/m2 K)
        Uv = self.Uv  # vapor phase film heat transfer coefficient (W/m2 K)
        Ui = (Ul * Uv) / (Ul + Uv)  # interface heat transfer coefficient (W/m2 K)
        Uvw = self.Uvw  # wall-vapor heat transfer coefficient (W/m2 K)
        Ulw = self.Ulw  # wall-liquid heat transfer coefficient (W/m2 K)
        Ur = self.Ur  # tank roof-vapor heat transfer coefficient (W/m2 K)
        Ub = self.Ub  # tank bottom-liquid heat transfer coefficient (W/m2 K)
        ## Optional
        nJ = [self.jacketStartValue/100, self.jacketEndValue/100]  # jacket location
        Uvr = self.Uvr  # jacket-vapor heat transfer coefficient (W/m2 K)
        Ulr = self.Ulr  # jacket-liquid side heat transfer coefficient (W/m2 K)
        Tj = self.refridgeTemp  # refrigerant temperature (K)


        def liq_prop(T):
            E = np.zeros((len(T), I))
            C = np.zeros((len(T), I))
            LD = np.zeros((len(T), I))
            for j in range(len(T)):
                for i in range(I):
                    component = importlib.import_module("components.{self.componentList[i]}")
                    if len(T) > 1:
                        E[j, i] = component.liq_enthalpy(np.atleast_2d(T[j]).T)[0]
                        C[j, i] = component.liq_heat_capacity(np.atleast_2d(T[j]).T)[0]
                        LD[j, i] = component.density(T[j][0])
                    elif len(T) == 1:
                        E[j, i] = component.liq_enthalpy([T])[0]
                        C[j, i] = component.liq_heat_capacity([T])[0]
                        LD[j, i] = component.density(T[j])
            return E, C, LD

        def vap_prop(T):
            Ei = np.zeros((len(T), I))
            Ci = np.zeros((len(T), I))
            for j in range(len(T)):
                for i in range(I):
                    component = importlib.import_module("components.{self.componentList[i]}")
                    if len(T) > 1:
                        Ei[j, i] = component.vap_enthalpy(np.atleast_2d(T[j]).T)[0]
                        Ci[j, i] = component.vap_heat_capacity(np.atleast_2d(T[j]).T)[0]
                    elif len(T) == 1:
                        Ei[j, i] = component.vap_enthalpy([T])[0]
                        Ci[j, i] = component.vap_heat_capacity([T])[0]
            return Ei, Ci

        def Vap_Pressure(T):
            P_s = np.zeros((len(T), I))
            for j in range(len(T)):
                for i in range(I):
                    component = importlib.import_module("components.{self.componentList[i]}")
                    P_s[j, i] = component.vapor_pressure(T[j])
            return P_s

        ## Initial conditions in the tank
        h0 = self.initialLiquidHeight * H/100  # liquid height (m) from a percentage of H
        P0 = self.initialPressure # tank pressure (kPa)
        self.noDisks = self.noLDisks + self.noVDisks
        T0 = self.diskinitCombined.iloc[:,1].to_numpy(dtype=float).reshape(-1,1)
        x0 = self.diskinitCombined.iloc[:, 2:].to_numpy(dtype=float)
        d0 = np.zeros((N, 1))  # disk density
        Ei, Ci, Di = liq_prop(T0[:NL])
        d0[:NL, 0] = 1 / np.sum((x0[:NL, :] / Di), axis=1)
        Pg = P0
        self.Pg = Pg
        AN1 = [x for x in x0[N-1,:]]
        AN2 = [Pg]
        AN3 = T0[N-1].tolist()
        AN = AN1 + AN2 + AN3
        AN = np.array(AN).reshape(1,-1)
        Z1 = ModelZg.ans(AN)
        Z = Z1[0][0]
        d0[NL:N, 0] = P0 / (Z * R * T0[N - 1]) / np.sum(x0[N - 1, :] / MW)
        W0 = np.zeros((I, N))
        W0[:, :NL] = d0[:NL, 0] * np.transpose(x0[:NL, :]) * (A * h0 / NL / Lref)
        W0[:, NL:N] = d0[NL:N, 0] * np.transpose(x0[NL:N, :]) * (A * (H - h0) / NV / Vref)
        y0 = np.zeros((NE, 1))
        y0[:N] = (T0 / Tref).tolist()
        y0[N:NC] = np.reshape(np.transpose(W0), (len(W0) * len(W0[0]), 1))

        ## Main Program
        t = [0]
        y = y0.reshape(1, -1)[0]  # horizontal list

        if F > 0:
            Fi = [self.Af_dict[key].iloc[0, 1] for key in self.Af_dict]
            FT = [self.Af_dict[key].iloc[0, 3] for key in self.Af_dict]
            FP = [self.Af_dict[key].iloc[0, 5] for key in self.Af_dict]
            Fz = []

        def mass(u):
            # global H, A, R, g, Z, MW, I, N, NL, NV, NE, NC, Tref, Vref, Lref, Ad, Bd, Cd, bi, Sp, Tmin, Tmax
            ### Model Variables
            u = np.array(u)
            u = u.reshape(-1, 1)
            T = u[0:N] * Tref
            Wn = np.transpose(np.reshape(u[N:NC], (int((NC - N) / I), I)))
            Wn[:, :NL] = Wn[:, :NL] * Lref
            Wn[:, NL:N] = Wn[:, NL:N] * Vref
            sumw = Wn.sum(axis=0)
            x = Wn / sumw

            ### Enthalpy calculations
            Ei = np.zeros((N, I))
            Ci = np.zeros((N, I))
            EL, CL, LD = liq_prop(T[:NL])
            EV, CV = vap_prop(T[NL:N])
            Ei[:NL, :] = EL
            Ei[NL:N, :] = EV
            Ei = Ei.T
            Ci[:NL, :] = CL
            Ci[NL:N, :] = CV

            CP = np.zeros((1, N))
            CP[0, 0:NL] = (x[:, :NL] * np.transpose(Ci[:NL, :])).sum(axis=0)
            CP[0, NL:N] = (x[:, NL:N] * np.transpose(Ci[NL:N, :])).sum(axis=0)

            ## Mass Matrix
            Mass = np.zeros((NE, NE))
            # Energy Balance
            for i in range(N):
                if i <= NL - 1:
                    Mass[i, i] = sumw[i] * CP[0, i] / Lref
                else:
                    Mass[i, i] = sumw[i] * CP[0, i] / Vref
                p = i + 1
                lowerlimit = N + (p - 1) * I
                upperlimit = N + (p) * I
                for j in range(lowerlimit, upperlimit):
                    k = j - (N + i * I)
                    Mass[i, j] = Ei[k, i] / Tref

            # Component Balance
            for i in range(N, NC):
                Mass[i, i] = 1

            return Mass

        def tankfunc(u, t):
            global ai
            u = np.array(u)
            # u = np.atleast_2d(u)
            u = u.reshape(-1, 1)
            dydt = np.zeros((NE, 1))
            ## Ambient Temperature
            t0 = (t / (24 * 3600)) % 24
            Ta = Tamb[0] + Tamb[1] * t0 + Tamb[2] * t0 ** 2
            # Model Variables
            T = u[0:N] * Tref
            Wn = np.transpose(np.reshape(u[N:NC], (int((NC - N) / I), I)))
            Wn[:, :NL] = Wn[:, :NL] * Lref
            Wn[:, NL:N] = Wn[:, NL:N] * Vref
            sumw = Wn.sum(axis=0)
            x = Wn / sumw
            wsq = np.zeros((N - 1, 1))
            wsq[:NL - 1] = u[NC:NC + NL - 1] * 0.01 * Lref
            wsq[NL:N - 1] = u[NC + NL - 1:NE] * 0.01 * Vref

            ### Density & Pressure
            rho = np.zeros((N, 1))
            P = np.zeros((N, 1))
            Mw = np.zeros((N, 1))
            EL, CL, LD = liq_prop(T[:NL])
            rho[:NL, 0] = 1 / (np.transpose(x[:, :NL]) / LD).sum(axis=1)
            h = NL * sumw[0] / A / rho[0, 0]  # liquid level
            Mw[:, 0] = 1 / (np.transpose(x[:, :N]) / MW).sum(axis=1)

            P1 = np.zeros((N-NL, 1))
            P1[:] = self.Pg
            zf = np.transpose(x[:, NL:N])
            AN = np.concatenate((zf, P1, T[NL:N].reshape(-1,1)), axis=1)
            BN = ModelZg.ans(AN)
            BN = np.maximum(BN, 0)
            BN_list = BN.reshape(1, -1).tolist()[0]
            Z = np.zeros((N,1))
            Z[NL:N, 0] = BN_list
            PV = (NV * Z[N-1] * R * T[N - 1, 0] * sumw[N - 1]) / (A * (H - h) * Mw[N - 1, 0])
            self.Pg = PV
            rho1 = PV * Mw[NL:N, 0]
            rho2 = (Z[NL:N, 0] * R * T[NL:N, 0])
            rho[NL:N, 0] = rho1/rho2
            P[NL:N, 0] = PV
            for i in range(NL):
                P[i] = PV + (g * h / NL) * (0.5 * rho[i] + rho[i + 1:NL].sum()) / 1000
            ## Enthalpy Calculations
            Ei = np.zeros((N, I))
            EL, CL, LD = liq_prop(T[:NL])
            EV, CV = vap_prop(T[NL:N])
            Ei[:NL, :] = EL
            Ei[NL:N, :] = EV
            E = np.zeros((1, N))
            E[0, 0:NL] = (Ei[:NL, :] * np.transpose(x[:, :NL])).sum(axis=1)
            E[0, NL:N] = (Ei[NL:N, :] * np.transpose(x[:, NL:N])).sum(axis=1)
            ## Interface Calculations
            T_I = (Ul * T[NL - 1, 0] + Uv * T[NL, 0]) / (Ul + Uv)
            X = np.transpose(x[:, NL - 1]) / MW / (np.transpose(x[:, NL - 1]) / MW).sum(axis=0)
            Y = np.transpose(x[:, NL]) / MW / (np.transpose(x[:, NL]) / MW).sum(axis=0)
            Ps = Vap_Pressure([T_I])
            K = np.maximum(Ps / PV, 1 * 10 ** (-6))
            ## Evaporation Flux Calculation
            J = sigma * A * PV * (np.minimum(K * X, 1) - Y) * np.sqrt(MW)
            e = np.maximum(J, 0)
            c = np.maximum(J * (-1), 0)
            TI_A = np.array([T_I])
            EL, CL, LD = liq_prop(TI_A)
            EV, CV = vap_prop(TI_A)
            sumc = np.matmul(c, np.transpose(EL))[0][0]
            sume = np.matmul(e, np.transpose(EV))[0][0]
            wsq[NL - 1] = np.sum(J)

            ### Flash stream
            ## Liquid and vapour distribution
            mf = np.zeros((F, 1))
            for r in range(F):
                if nf[r] > h:
                    mf[r, 0] = np.round((nf[r] - h) / ((H - h) / NV)) + NL
                else:
                    mf[r, 0] = np.maximum(np.round(nf[r] / (h / NL)), 1)

            ## Flowrate, Temperature and Vapor Fraction
            if F > 0:
                Tf = np.array([np.array(ATf), np.array(BTf) * t]).sum(axis=0)
                Pf = np.array([np.array(APf), np.array(BPf) * t]).sum(axis=0)
                Fi = np.array([np.array(Af), np.array(Bf) * t]).sum(axis=0)
                zf = np.array([np.array(AZf), np.array(BZf) * t]).sum(axis=0)
                Ff = np.transpose(np.reshape(Fi, (-1, len(Fi)))) * zf
                Pf = Pf.reshape(-1, 1)
                mf_1 = mf.reshape(1, -1)[0].tolist()
                mf_1 = [int(i)-1 for i in mf_1]
                P_mf = P[mf_1]
                Tf = Tf.reshape(-1, 1)
                AN = np.concatenate((zf, Pf, P_mf, Tf), axis=1)
                BN = np.maximum(ModelF.ANN(AN), 0)
                T2 = BN[:, 0]
                vf = np.minimum(BN[:, 1:], zf)
                fv = vf * Ff
                fl = Ff - fv
                T2_1 = T2.reshape(-1, 1)
                EL, Ci, Di = liq_prop(T2_1)
                EV, Ci = vap_prop(T2_1)
                fel = np.sum((fl * EL), axis=1)
                fev = np.sum((fv * EV), axis=1)
                fel = fel.reshape(-1, 1)  # column vector
                fev = fev.reshape(-1, 1)  # column vector

            ## Liquid and Vapour Distributions
            ff = np.zeros((N, F))
            for r in range(F):
                if mf[r, 0] > NL:
                    xp = [i for i in range(NL)]
                    ldf = poisson.pmf(xp, mu=1)
                    yp = [i for i in range(N - int(mf[r, 0]) + 1)]
                    vdf = poisson.pmf(yp, mu=1)
                    xp = [i for i in range(int(mf[r, 0]) - NL)]
                    xpf = poisson.pmf(xp, mu=1)
                    for i in range(N):
                        if i <= NL - 1:
                            ff[i, r] = ldf[NL - i - 1]
                        elif i > NL - 1 and i < int(mf[r, 0]) - 1:
                            ff[i, r] = xpf[int(mf[r, 0]) - i - 2]
                        else:
                            # print(i, vdf[i-int(mf.iloc[r, 0])])
                            ff[i, r] = vdf[i - int(mf[r, 0]) + 1]

                elif mf[r, 0] == NL:
                    xp = [i for i in range(NL)]
                    ldf = poisson.pmf(xp, mu=1)
                    yp = [i for i in range(N - NL)]
                    vdf = poisson.pmf(yp, mu=1)
                    for i in range(N):
                        if i <= NL - 1:
                            ff[i, r] = ldf[NL - i - 1]
                        else:
                            ff[i, r] = vdf[i - NL]

                else:
                    xp = [i for i in range(int(mf[r, 0]))]
                    ldf = poisson.pmf(xp, mu=1)
                    xp = [i for i in range(NL - int(mf[r, 0]))]
                    vdf = poisson.pmf(xp, mu=1)
                    for i in range(N):
                        if i <= int(mf[r, 0]) - 1:
                            ff[i, r] = ldf[int(mf[r, 0]) - i - 1]
                        elif i > int(mf[r, 0]) - 1 and i <= NL - 1:
                            ff[i, r] = vdf[i - int(mf[r, 0])]
                        else:
                            ff[i, r] = 0

            ff[:NL, :] = ff[:NL, :] / ff[:NL, :].sum(axis=0)
            ff[NL:N, :] = ff[NL:N, :] / ff[NL:N, :].sum(axis=0)
            ff = np.maximum(ff, 0)
            ff = np.nan_to_num(ff)

            # ## Send Out Stream
            if S > 0:
                Gi = np.array(Ag) + np.array(Bg) * t
                mg = np.zeros((S, 1))
                for s in range(S):
                    if ng[s] > h:
                        mg[s, 0] = np.round((ng[s] - h) / ((H - h) / NV)) + NL
                    else:
                        mg[s, 0] = np.maximum(np.round(ng[s] / (h / NL)), 1)

                pf = np.zeros((N, S))
                for s in range(S):
                    if mg[s, 0] <= NL:
                        xp = [i for i in range(int(mg[s, 0]))]
                        ldf = poisson.pmf(xp, mu=1)
                        xp = [i for i in range(NL - int(mg[s, 0]))]
                        vdf = poisson.pmf(xp, mu=1)
                        for i in range(N):
                            if i <= mg[s, 0] - 1:
                                pf[i, s] = ldf[int(mg[s, 0]) - i - 1]
                            elif i > mg[s, 0] - 1 and i <= NL - 1:
                                pf[i, s] = vdf[i - int(mg[s, 0])]
                            else:
                                pf[i, s] = 0

                    else:
                        xp = [i for i in range(int(mg[s, 0]) - NL)]
                        ldf = poisson.pmf(xp, mu=1)
                        xp = [i for i in range(N - int(mg[s, 0] + 1))]
                        vdf = poisson.pmf(xp, mu=1)
                        for i in range(N):
                            if i <= NL - 1:
                                pf[i, s] = 0
                            elif i > NL - 1 and i <= mg[s, 0] - 1:
                                pf[i, s] = ldf[int(mg[s, 0]) - i - 1]
                            else:
                                pf[i, s] = vdf[i - int(mg[s, 0])]

                pf[:NL, :] = pf[:NL, :] / pf[:NL, :].sum(axis=0)
                pf[NL:N, :] = pf[NL:N, :] / pf[NL:N, :].sum(axis=0)
                pf = np.maximum(pf, 0)
                pf = np.nan_to_num(pf)
                sumg = np.matmul(pf, np.transpose(Gi))

            ### Heat Transfer Calculations
            ## Jacket Location
            mJ = np.zeros((2, 1))
            for l in range(2):
                if nJ[l] > h - 1:
                    mJ[l, 0] = np.round((nJ[l] - h) / ((H - h) / NV)) + NL
                else:
                    mJ[l, 0] = np.maximum(np.round(nJ[l] / (h / NL)), 1)

            ## Heat leak from surrounding
            Q = np.zeros((N, 1))
            q = np.zeros((N, 1))
            for i in range(N):
                if mJ[0, 0] < NL:
                    if mJ[1, 0] + 1 <= NL:
                        if i >= mJ[0, 0]-1 and i <= mJ[1, 0]-1:
                            Q[i, 0] = Ulr * math.pi * D * h * (Tj - T[i, 0]) / NL
                        elif i > NL - 1:
                            Q[i, 0] = Uvw * math.pi * D * (H - h) * (Ta - T[i, 0]) / NV
                        else:
                            Q[i, 0] = Ulw * math.pi * D * h * (Ta - T[i, 0]) / NL

                    else:
                        if i < mJ[0, 0] - 1:
                            Q[i, 0] = Ulw * math.pi * D * h * (Ta - T[i, 0]) / NL
                        elif i >= mJ[0, 0] - 1 and i <= NL - 1:
                            Q[i, 0] = Ulr * math.pi * D * h * (Tj - T[i, 0]) / NL
                        elif i > NL - 1 and i <= mJ[1, 0] - 1:
                            Q[i, 0] = Uvr * math.pi * D * (H - h) * (Tj - T[i, 0]) / NV
                        else:
                            Q[i, 0] = Uvr * math.pi * D * (H - h) * (Ta - T[i, 0]) / NV
                else:
                    if i >= mJ[0, 0] - 1 and i <= mJ[1, 0] - 1:
                        Q[i, 0] = Uvr * math.pi * D * (H - h) * (Tj - T[i, 0]) / NV
                    elif i <= NL - 1:
                        Q[i, 0] = Ulw * math.pi * D * h * (Ta - T[i, 0]) / NL
                    else:
                        Q[i, 0] = Uvw * math.pi * D * (H - h) * (Ta - T[i, 0]) / NV

            # Heat Transfer across Disks
            q[0, 0] = Ub * A * (Tb - T[0, 0]) - Ul * A * (T[0, 0] - T[1, 0])
            q[1:NL - 1, 0] = Ul * A * (T[:NL - 2, 0] - T[1:NL - 1, 0]) - Ul * A * (T[1:NL - 1, 0] - T[2:NL, 0])
            q[NL - 1, 0] = Ul * A * (T[NL - 2, 0] - T[NL - 1, 0]) - Ui * A * (T[NL - 1, 0] - T[NL, 0])
            q[NL, 0] = Ui * A * (T[NL - 1, 0] - T[NL, 0]) - Uv * A * (T[NL, 0] - T[NL + 1, 0])
            q[NL + 1:N - 1, 0] = Uv * A * (T[NL:N - 2, 0] - T[NL + 1:N - 1, 0]) - Uv * A * (
                    T[NL + 1:N - 1, 0] - T[NL + 2:N, 0])
            q[N - 1, 0] = Uv * A * (T[N - 2, 0] - T[N - 1, 0]) + Ur * A * (Tr - T[N - 1, 0])

            ## Energy Balance
            if F > 0 and S > 0:
                for i in range(NL):
                    if i == 0:
                        dydt[i] = np.matmul(ff[i, :], fel[:, 0]) - sumg[i] * E[0, i] - np.maximum(wsq[i, 0], 0) * E[
                            0, i] + \
                                    np.maximum(wsq[i, 0] * -1, 0) * E[0, i + 1] + q[i, 0] + Q[i, 0]
                    elif i == NL - 1:
                        dydt[i] = np.matmul(ff[i, :], fel[:, 0]) - sumg[i] * E[0, i] + np.maximum(wsq[i - 1, 0], 0) * E[
                            0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * -1, 0) * E[0, i] + sumc - sume + q[i, 0] + Q[i, 0]
                    else:
                        dydt[i] = np.matmul(ff[i, :], fel[:, 0]) - sumg[i] * E[0, i] + np.maximum(wsq[i - 1, 0], 0) * E[
                            0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * -1, 0) * E[0, i] - np.maximum(wsq[i, 0], 0) * E[
                                        0, i] + np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + \
                                    q[i, 0] + Q[i, 0]

            elif F == 0 and S > 0:
                for i in range(NL):
                    if i == 0:
                        dydt[i] = -sumg[i] * E[0, i] - np.maximum(wsq[i, 0], 0) * E[0, i] + \
                                    np.maximum(wsq[i, 0] * -1, 0) * E[0, i + 1] + q[i, 0] + Q[i, 0]
                    elif i == NL - 1:
                        dydt[i] = -sumg[i] * E[0, i] + np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * -1, 0) * E[0, i] + sumc - sume + q[i, 0] + Q[i, 0]
                    else:
                        dydt[i] = -sumg[i] * E[0, i] + np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * -1, 0) * E[0, i] - np.maximum(wsq[i, 0], 0) * E[0, i] \
                                    + np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + q[i, 0] + Q[i, 0]

            elif F > 0 and S == 0:
                for i in range(NL):
                    if i == 0:
                        dydt[i] = np.matmul(ff[i, :], fel[:, 0]) - np.maximum(wsq[i, 0], 0) * E[0, i] + \
                                    np.maximum(wsq[i, 0] * -1, 0) * E[0, i + 1] + q[i, 0] + Q[i, 0]
                    elif i == NL - 1:
                        dydt[i] = np.matmul(ff[i, :], fel[:, 0]) + np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * -1, 0) * E[0, i] + sumc - sume + q[i, 0] + Q[i, 0]
                    else:
                        dydt[i] = np.matmul(ff[i, :], fel[:, 0]) + np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * -1, 0) * E[0, i] - np.maximum(wsq[i, 0], 0) * E[0, i] \
                                    + np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + q[i, 0] + Q[i, 0]

            elif F == 0 and S == 0:
                for i in range(NL):
                    if i == 0:
                        dydt[i] = - np.maximum(wsq[i, 0], 0) * E[0, i] + np.maximum(wsq[i, 0] * -1, 0) * E[0, i + 1]\
                                    + q[i, 0] + Q[i, 0]
                    elif i == NL - 1:
                        dydt[i] = np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * -1, 0) * E[0, i] + sumc - sume + q[i, 0] + Q[i, 0]
                    else:
                        dydt[i] = np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * -1, 0) * E[0, i] - np.maximum(wsq[i, 0], 0) * E[0, i] \
                                    + np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + q[i, 0] + Q[i, 0]

            dydt[:NL] = dydt[:NL] / (Lref * Tref)

            if F > 0 and S > 0:
                for i in range(NL, N):
                    if i == NL:
                        dydt[i] = np.matmul(ff[i, :], fev[:, 0]) - sumg[i] * E[0, i] - np.maximum(wsq[i, 0], 0) * E[
                            0, i] + \
                                    np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + sume + sumc + q[i, 0] + Q[i, 0]
                    elif i == N - 1:
                        dydt[i] = np.matmul(ff[i, :], fev[:, 0]) - sumg[i] * E[0, i] + np.maximum(wsq[i - 1, 0], 0) * E[
                            0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * (-1), 0) * E[0, i] + q[i, 0] + Q[i, 0]
                    else:
                        dydt[i] = np.matmul(ff[i, :], fev[:, 0]) - sumg[i] * E[0, i] + np.maximum(wsq[i - 1, 0], 0) * E[
                            0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * (-1), 0) * E[0, i] - np.maximum(wsq[i, 0], 0) * E[0, i] + \
                                    np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + q[i, 0] + Q[i, 0]

            elif F > 0 and S == 0:
                for i in range(NL, N):
                    if i == NL:
                        dydt[i] = np.matmul(ff[i, :], fev[:, 0]) - np.maximum(wsq[i, 0], 0) * E[0, i] + \
                                    np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + sume + sumc + q[i, 0] + Q[i, 0]
                    elif i == N - 1:
                        dydt[i] = np.matmul(ff[i, :], fev[:, 0]) + np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * (-1), 0) * E[0, i] + q[i, 0] + Q[i, 0]
                    else:
                        dydt[i] = np.matmul(ff[i, :], fev[:, 0]) + np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * (-1), 0) * E[0, i] - np.maximum(wsq[i, 0], 0) * E[0, i] + \
                                    np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + q[i, 0] + Q[i, 0]

            elif F == 0 and S > 0:
                for i in range(NL, N):
                    if i == NL:
                        dydt[i] = -sumg[i] * E[0, i] - np.maximum(wsq[i, 0], 0) * E[0, i] + \
                                    np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + sume + sumc + q[i, 0] + Q[i, 0]
                    elif i == N - 1:
                        dydt[i] = -sumg[i] * E[0, i] + np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * (-1), 0) * E[0, i] + q[i, 0] + Q[i, 0]
                    else:
                        dydt[i] = -sumg[i] * E[0, i] + np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * (-1), 0) * E[0, i] - np.maximum(wsq[i, 0], 0) * E[0, i] + \
                                    np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + q[i, 0] + Q[i, 0]

            elif F == 0 and S == 0:
                for i in range(NL, N):
                    if i == NL:
                        dydt[i] = -np.maximum(wsq[i, 0], 0) * E[0, i] + \
                                    np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + sume + sumc + q[i, 0] + Q[i, 0]
                    elif i == N - 1:
                        dydt[i] = np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * (-1), 0) * E[0, i] + q[i, 0] + Q[i, 0]
                    else:
                        dydt[i] = np.maximum(wsq[i - 1, 0], 0) * E[0, i - 1] - \
                                    np.maximum(wsq[i - 1, 0] * (-1), 0) * E[0, i] - np.maximum(wsq[i, 0], 0) * E[0, i] + \
                                    np.maximum(wsq[i, 0] * (-1), 0) * E[0, i + 1] + q[i, 0] + Q[i, 0]

            dydt[NL:N] = dydt[NL:N] / (Vref * Tref)

            # Component Balance
            num1 = int(N + (NL * I))
            if F > 0 and S > 0:
                for i in range(N, num1):
                    i2 = i + 1
                    n = int(1 + np.floor((i2 - 1 - N) / I))
                    j = int(i2 - N - (n - 1) * I)
                    if n == 1:
                        dydt[i] = np.matmul(ff[n - 1, :], fl[:, j - 1]) - sumg[n - 1] * x[j - 1, n - 1] - np.maximum(
                            wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n]
                    elif n == NL:
                        dydt[i] = np.matmul(ff[n - 1, :], fl[:, j - 1]) - sumg[n - 1] * x[j - 1, n - 1] - e[0][j - 1] + \
                                    c[0][j - 1] + np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]
                    else:
                        dydt[i] = np.matmul(ff[n - 1, :], fl[:, j - 1]) - sumg[n - 1] * x[j - 1, n - 1] - np.maximum(
                            wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + np.maximum(wsq[n - 2, 0], 0) * x[
                                        j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]

            elif F > 0 and S == 0:
                for i in range(N, num1):
                    i2 = i + 1
                    n = int(1 + np.floor((i2 - 1 - N) / I))
                    j = int(i2 - N - (n - 1) * I)
                    if n == 1:
                        dydt[i] = np.matmul(ff[n - 1, :], fl[:, j - 1]) - np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n]
                    elif n == NL:
                        dydt[i] = np.matmul(ff[n - 1, :], fl[:, j - 1]) - e[0][j - 1] + \
                                    c[0][j - 1] + np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]
                    else:
                        dydt[i] = np.matmul(ff[n - 1, :], fl[:, j - 1]) - np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + \
                                    np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]

            elif F == 0 and S > 0:
                for i in range(N, num1):
                    i2 = i + 1
                    n = int(1 + np.floor((i2 - 1 - N) / I))
                    j = int(i2 - N - (n - 1) * I)
                    if n == 1:
                        dydt[i] = -sumg[n - 1] * x[j - 1, n - 1] - np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n]
                    elif n == NL:
                        dydt[i] = -sumg[n - 1] * x[j - 1, n - 1] - e[0][j - 1] + c[0][j - 1] + \
                                    np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]
                    else:
                        dydt[i] = -sumg[n - 1] * x[j - 1, n - 1] - np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + \
                                    np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]

            elif F == 0 and S == 0:
                for i in range(N, num1):
                    i2 = i + 1
                    n = int(1 + np.floor((i2 - 1 - N) / I))
                    j = int(i2 - N - (n - 1) * I)
                    if n == 1:
                        dydt[i] = -np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n]
                    elif n == NL:
                        dydt[i] = -e[0][j - 1] + c[0][j - 1] + np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]
                    else:
                        dydt[i] = -np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + \
                                    np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]

            dydt[N:num1] = dydt[N:num1] / Lref

            if F > 0 and S > 0:
                for i in range(num1, NC):
                    i2 = i + 1
                    n = int(1 + np.floor((i2 - 1 - N) / I))
                    j = int(i2 - N - (n - 1) * I)
                    if n == NL + 1:
                        dydt[i] = np.matmul(ff[n - 1, :], fv[:, j - 1]) - sumg[n - 1] * x[j - 1, n - 1] - np.maximum(
                            wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + e[0][j - 1] - c[0][j - 1]
                    elif n == N:
                        dydt[i] = np.matmul(ff[n - 1, :], fv[:, j - 1]) - sumg[n - 1] * x[j - 1, n - 1] + np.maximum(
                            wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]
                    else:
                        dydt[i] = np.matmul(ff[n - 1, :], fv[:, j - 1]) - sumg[n - 1] * x[j - 1, n - 1] - np.maximum(
                            wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + np.maximum(wsq[n - 2, 0], 0) * x[
                                        j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]

            elif F > 0 and S == 0:
                for i in range(num1, NC):
                    i2 = i + 1
                    n = int(1 + np.floor((i2 - 1 - N) / I))
                    j = int(i2 - N - (n - 1) * I)
                    if n == NL + 1:
                        dydt[i] = np.matmul(ff[n - 1, :], fv[:, j - 1]) - np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + e[0][j - 1] - c[0][j - 1]
                    elif n == N:
                        dydt[i] = np.matmul(ff[n - 1, :], fv[:, j - 1]) + np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]
                    else:
                        dydt[i] = np.matmul(ff[n - 1, :], fv[:, j - 1]) - np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + \
                                    np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]

            elif F == 0 and S > 0:
                for i in range(num1, NC):
                    i2 = i + 1
                    n = int(1 + np.floor((i2 - 1 - N) / I))
                    j = int(i2 - N - (n - 1) * I)
                    if n == NL + 1:
                        dydt[i] = -sumg[n - 1] * x[j - 1, n - 1] - np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + e[0][j - 1] - c[0][j - 1]
                    elif n == N:
                        dydt[i] = -sumg[n - 1] * x[j - 1, n - 1] + np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]
                    else:
                        dydt[i] = -sumg[n - 1] * x[j - 1, n - 1] - np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + \
                                    np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]

            elif F == 0 and S == 0:
                for i in range(num1, NC):
                    i2 = i + 1
                    n = int(1 + np.floor((i2 - 1 - N) / I))
                    j = int(i2 - N - (n - 1) * I)
                    if n == NL + 1:
                        dydt[i] = -np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + e[0][j - 1] - c[0][j - 1]
                    elif n == N:
                        dydt[i] = np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]
                    else:
                        dydt[i] = -np.maximum(wsq[n - 1, 0], 0) * x[j - 1, n - 1] + \
                                    np.maximum(wsq[n - 1, 0] * (-1), 0) * x[j - 1, n] + \
                                    np.maximum(wsq[n - 2, 0], 0) * x[j - 1, n - 2] - \
                                    np.maximum(wsq[n - 2, 0] * (-1), 0) * x[j - 1, n - 1]

            dydt[num1:NC] = dydt[num1:NC] / Vref

            ## Interdisk flows
            dydt[NC:NC + NL - 1] = np.transpose(sumw[1:NL][np.newaxis]) / sumw[0] - rho[1:NL] / rho[0, 0]
            dydt[NC + NL - 1:NE] = np.transpose(sumw[NL:N - 1][np.newaxis]) / sumw[N - 1] - rho[NL:N - 1] / rho[
                N - 1, 0]

            # ai = ai + 1
            TE = np.matmul(sumw, np.transpose(E))[0]

            return dydt

        def f(t, u, du):
            du_array = np.atleast_2d(du).T
            M = mass(u)
            rhs_du = tankfunc(u, t)
            lhs_du = np.matmul(M, du_array)
            resid = rhs_du - lhs_du
            resid = resid.tolist()
            resid = [x[0] for x in resid]
            resid = np.array(resid)
            return resid

        numberofIterations = int(self.numberofIterations/5)
        for r in range(numberofIterations):
            print(r+1)
            Af = []
            Bf = []
            AZf = []
            BZf = []
            ATf = []
            BTf = []
            APf = []
            BPf = []
            if F > 0:
                for i in range(F):
                    Af.append(self.Af_dict['Af({})'.format(str(i + 1))]['Af({})'.format(str(i + 1))][r])
                    Bf.append(self.Af_dict['Af({})'.format(str(i + 1))]['Bf({})'.format(str(i + 1))][r])
                    AZ_df = self.AZ_dict['AZ({})'.format(str(i + 1))]
                    AZf.append(AZ_df.iloc[r, :].values.tolist())
                    BZ_df = self.BZ_dict['BZ({})'.format(str(i + 1))]
                    BZf.append(BZ_df.iloc[r, :].values.tolist())
                    ATf.append(self.Af_dict['Af({})'.format(str(i + 1))]['ATf({})'.format(str(i + 1))][r])
                    BTf.append(self.Af_dict['Af({})'.format(str(i + 1))]['BTf({})'.format(str(i + 1))][r])
                    APf.append(self.Af_dict['Af({})'.format(str(i + 1))]['APf({})'.format(str(i + 1))][r])
                    BPf.append(self.Af_dict['Af({})'.format(str(i + 1))]['BPf({})'.format(str(i + 1))][r])

            Ag = []
            Bg = []
            if S > 0:
                for i in range(S):
                    Ag.append(self.Ag_dict['Ag({})'.format(str(i + 1))]['Ag({})'.format(str(i + 1))][r])
                    Bg.append(self.Ag_dict['Ag({})'.format(str(i + 1))]['Bg({})'.format(str(i + 1))][r])
                    # Ag.append(self.Ag_dict['Ag({})'.format(str(i + 1))]['Ag({})'.format(str(i + 1))][0])
                    # Bg.append(self.Ag_dict['Ag({})'.format(str(i + 1))]['Bg({})'.format(str(i + 1))][0])
            p = np.ones((1, NE))
            tspan = (0.0, 300.0)

            if r == 0:
                y0 = [y0[i, 0] for i in range(len(y0))]
            else:
                y0 = y[-1, :].reshape(1, -1)[0]

            dy0 = np.matmul(np.linalg.pinv(mass(y0)), tankfunc(y0, 0))
            dy0 = [dy0[i, 0] for i in range(len(dy0))]

            nondiffEq = NE-8
            abstol = self.abstol
            reltol = self.reltol
            differential_vars = np.append(np.ones((1, nondiffEq), dtype=bool), np.zeros((1, 8), dtype=bool))
            differential_vars = [x for x in differential_vars]

            model = Implicit_Problem(f, y0, dy0, 0)
            sim = IDA(model)
            sim.atol = abstol
            sim.rtol = reltol
            sim.algvar = differential_vars
            tfinal = 300.0
            ncp = 10
            t2, y2, yd = sim.simulate(tfinal, ncp)

            t2 = np.atleast_2d(t2).T

            ## Feed Flash Calculations
            if F > 0:
                if r == 0:
                    Fi = np.array(Fi).reshape(1, -1)
                Af_term = Af + Bf * t2[1:]
                Fi = np.append(Fi, Af_term, axis=0)

                if r == 0:
                    FT = np.array(FT).reshape(1, -1)
                ATf_term = ATf + BTf * t2[1:]
                FT = np.append(FT, ATf_term, axis=0)

                if r == 0:
                    FP = np.array(FP).reshape(1, -1)
                APf_term = APf + BPf * t2[1:]
                FP = np.append(FP, APf_term, axis=0)

                if r == 0:
                    dFz = np.zeros((F, len(t2), I))
                    for j in range(F):
                        for p in range(len(t2)):
                            dFz[j, p, :] = AZf[j] + BZf[j] * t2[p]
                else:
                    dFz = np.zeros((F, len(t2) - 1, I))
                    for j in range(F):
                        for p in range(len(t2) - 1):
                            dFz[j, p, :] = AZf[j] + BZf[j] * t2[p + 1]

                dFz = np.transpose(dFz, (1, 0, 2))
                if r == 0:
                    Fz = dFz
                else:
                    Fz = np.append(Fz, dFz, axis=0)

            if r == 0:
                t = t2
                y = y2
            else:
                t2 = t2[1:] + t[-1]
                y2 = y2[1:, :]
                t = np.append(t, t2, axis=0)
                y = np.append(y, y2, axis=0)

        try:
            now2 = datetime.now()
            current_time = now2.strftime("%H:%M:%S")
            print("Done at", current_time)
            ### for generatefun
            self.t = t
            self.y = y
            self.N = N
            self.Tref = Tref
            self.NL = NL
            self.NC = NC
            self.NE = NE
            self.Lref = Lref
            self.Vref = Vref
            self.I = I
            self.A = A
            self.MW = MW
            self.NV = NV
            self.Z = Z
            self.R = R
            self.g = g
            self.Ul = Ul
            self.Uv = Uv
            self.sigma = sigma
            if F > 0:
                self.F = F
                self.Fz = Fz
                self.FP = FP
                self.FT = FT
                self.Fi = Fi
            else:
                self.F = 0
            self.H = H
            self.P0 = P0
            self.S = S
            self.ng = ng
            self.generatefun()
        except:
            pass

    def generatefun(self):
        ### from analyse
        if self.F > 0:
            F = self.F # no of feed streams
        else:
            F = 0
        t = self.t
        y = self.y
        N = self.N
        Tref = self.Tref
        NL = self.NL
        NC = self.NC
        NE = self.NE
        Lref = self.Lref
        Vref = self.Vref
        I = self.I
        A = self.A
        MW = self.MW
        NV = self.NV
        # Z = self.Z
        R = self.R
        g = self.g
        Ul = self.Ul
        Uv = self.Uv
        sigma = self.sigma
        if F > 0:
            Fz = self.Fz
            FP = self.FP
            FT = self.FT
            Fi = self.Fi
        H = self.H
        P0 = self.P0
        S = self.S
        ng = self.ng

        def liq_prop(T):
            E = np.zeros((len(T), I))
            C = np.zeros((len(T), I))
            LD = np.zeros((len(T), I))
            for j in range(len(T)):
                for i in range(I):
                    component = importlib.import_module("components.{self.componentList[i]}")
                    if len(T) > 1:
                        E[j, i] = component.liq_enthalpy(np.atleast_2d(T[j]).T)[0]
                        C[j, i] = component.liq_heat_capacity(np.atleast_2d(T[j]).T)[0]
                        LD[j, i] = component.density(T[j][0])
                    elif len(T) == 1:
                        E[j, i] = component.liq_enthalpy([T])[0]
                        C[j, i] = component.liq_heat_capacity([T])[0]
                        LD[j, i] = component.density(T[j])
            return E, C, LD

        def Vap_Pressure(T):
            P_s = np.zeros((len(T), I))
            for j in range(len(T)):
                for i in range(I):
                    component = importlib.import_module("components.{self.componentList[i]}")
                    P_s[j, i] = component.vapor_pressure(T[j])
            return P_s

        ## Results
        t = t / (24 * 3600)
        sy_m = len(y)
        sy_n = len(y[0])
        T = y[:, :N] * Tref
        wsq = np.zeros((sy_m, N - 1))
        wsq[:, :NL - 1] = y[:, NC:NC + NL - 1] * 0.01 * Lref
        wsq[:, NL:N - 1] = y[:, NC + NL - 1:NE] * 0.01 * Vref
        x = np.zeros((sy_m, I, N))
        Wn = np.zeros((sy_m, I, N))
        for i in range(N):
            Wn[:, :, i] = y[:, int(N + I * i):int(N + I * i + I)]
        Wn[:, :, :NL] = Wn[:, :, :NL] * Lref
        Wn[:, :, NL:N] = Wn[:, :, NL:N] * Vref
        sumw = Wn.sum(axis=1)  # equivalent to permute
        for i in range(x.shape[2]):
            mat = Wn[:, :, i]
            summation = mat.sum(axis=1).reshape(-1, 1)
            x[:, :, i] = mat / summation

        # %% ***Density and Pressure Computation****
        rho = np.zeros((sy_m, N))
        P = np.zeros((sy_m, N))
        h = np.zeros((sy_m, 1))
        PV = np.zeros((sy_m, 1))
        Z = np.zeros((sy_m, N))
        for i in range(N):
            if i <= NL - 1:
                T_arr = T[:, i].reshape(-1, 1)
                EL, CL, LD = liq_prop(T_arr)
                rho[:, i] = 1 / np.sum(x[:, :, i] / LD, axis=1)
                if i == 0:
                    h = (NL * sumw[:, i]) / A / rho[:, i]  # liquid level
                    Mw = 1 / np.sum(x[:, :, N - 1] / MW, axis=1)
                    ## Zg and PV calculation
                    Pg = P0
                    for sy in range(sy_m):
                        P1 = np.zeros((N - NL, 1))
                        P1[:] = Pg
                        T1 = np.array(T[sy, NL:N]).reshape(-1, 1)
                        zf = x[sy, :, NL:N]  # 4 by 5 array
                        zf = np.transpose(zf)  # 5 by 4 array
                        AN = np.concatenate((zf, P1, T1), axis=1)
                        BN = ModelZg.ans(AN)
                        BN = np.maximum(BN, 0)
                        BN_list = BN.reshape(1, -1).tolist()[0]
                        Z[sy, NL:N] = BN_list
                        PV[sy] = (NV * Z[sy, N - 1] * R * T[sy, N - 1] * sumw[sy, N - 1]) / (A * (H - h[sy]) * Mw[sy])
                        Pg = PV[sy]

            else:
                Mw = 1 / np.sum(x[:, :, i] / MW, axis=1)
                rho1 = PV * Mw.reshape(-1, 1)
                rho2 = Z[:, i] * R * T[:, i]
                rho2 = rho2.reshape(-1, 1)
                rho3 = rho1 / rho2
                rho3 = rho3.reshape(1, -1)[0]
                rho[:, i] = rho3
                PV_list = PV.reshape(1, -1)[0]
                P[:, i] = PV_list  # vapor phase pressure

        for i in range(NL):
            firstP = PV
            firstP = firstP.reshape(1, -1)[0]
            secondP = (g * h / NL) * (0.5 * rho[:, i] + np.sum(rho[:, i + 1:NL], axis=1)) / 1000
            ansP = firstP + secondP
            P[:, i] = ansP

        # %% *** Evaporation Flux Calculation ***
        T_I = (Ul * T[:, NL - 1] + Uv * T[:, NL]) / (Ul + Uv)  # Interface Temperature
        X = (x[:, :, NL - 1] / MW) / (np.sum(x[:, :, NL - 1] / MW, axis=1).reshape(-1, 1))
        Y = (x[:, :, NL] / MW) / (np.sum(x[:, :, NL] / MW, axis=1).reshape(-1, 1))
        Ps = np.maximum(Vap_Pressure(T_I), 0)
        K = np.maximum(Ps / PV.reshape(-1, 1), 1 * 10 ** (-6))
        J = sigma * A * PV.reshape(-1, 1) * (np.minimum(K * X, 1) - Y) * np.sqrt(MW)
        wsq[:, NL - 1] = np.sum(J, axis=1)

        P2 = np.zeros((F, 1))
        if F > 0:
            Fz = np.transpose(Fz, (1, 2, 0))
            for i in range(sy_m):
                P2[:, 0] = PV[i]
                AN = np.concatenate((Fz[:, :, i], FP[i, :].reshape(-1, 1), P2, FT[i, :].reshape(-1, 1)), axis=1)
                BN = np.maximum(ModelF.ANN(AN), 0)
                T2 = BN[:, 0]
                vf = np.minimum(BN[:, 1:], Fz[:, :, i])
                fv = vf * Fi[i, 0]
                fl = Fi[i, 0] - fv
                if i == 0:
                    VFL = np.array([np.sum(fl, axis=0).sum()]).reshape(-1, 1)
                    VFV = np.array([np.sum(fv, axis=0).sum()]).reshape(-1, 1)
                    TF = T2.reshape(1, -1)
                else:
                    VFL = np.append(VFL, np.array([np.sum(fl, axis=0).sum()]).reshape(-1, 1), axis=0)
                    VFV = np.append(VFV, np.array([np.sum(fv, axis=0).sum()]).reshape(-1, 1), axis=0)
                    TF = np.append(TF, T2.reshape(1, -1), axis=0)

            VF = VFV + wsq[:, NL - 1].reshape(-1,1)

        elif F == 0:
            VF = wsq[:, NL - 1].reshape(-1,1)


        ### Compositions for Plotting
        for i in range(N):
            if i == 0:
                xc = x[:, :, i]
                Wni = Wn[:, :, i]
            else:
                xc = np.append(xc, x[:, :, i], axis=1)
                Wni = np.append(Wni, Wn[:, :, i], axis=1)

        Tl_avg = (T[:, :NL].sum(axis=1))/NL  # Average liquid temperature
        Tv_avg = (T[:, NL:N]).sum(axis=1)/NV  # Average vapour temperature
        xl = np.zeros((sy_m,I))
        xv = np.zeros((sy_m,I))
        for i in range(I):
            xl[:,i] = x[:,i,:NL].sum(axis=1)/NL
            xv[:,i] = x[:,i, NL:N].sum(axis=1)/NV

        ### Product Stream Calculations
        Ts = np.zeros((sy_m, S))
        Ps = np.zeros((sy_m, S))
        xs = np.zeros((sy_m, I, S))
        for j in range(sy_m):
            mg = np.zeros((S, 1))
            for s in range(S):
                if ng[s] > h[j]:
                    mg[s] = np.round((ng[s]-h[j])/((H-h[j])/NV))+NL
                else:
                    mg[s] = np.maximum(np.round(ng[s]/(h[j]/NL)), 1)

            pf = np.zeros((N, S))
            for s in range(S):
                if mg[s, 0] <= NL:
                    xp = [i for i in range(int(mg[s, 0]))]
                    ldf = poisson.pmf(xp, mu=1)
                    xp = [i for i in range(NL - int(mg[s, 0]))]
                    vdf = poisson.pmf(xp, mu=1)
                    for i in range(N):
                        if i <= mg[s, 0] - 1:
                            pf[i, s] = ldf[int(mg[s, 0]) - i - 1]
                        elif i > mg[s, 0] - 1 and i <= NL - 1:
                            pf[i, s] = vdf[i - int(mg[s, 0])]
                        else:
                            pf[i, s] = 0

                else:
                    xp = [i for i in range(int(mg[s, 0]) - NL)]
                    ldf = poisson.pmf(xp, mu=1)
                    xp = [i for i in range(N - int(mg[s, 0] + 1))]
                    vdf = poisson.pmf(xp, mu=1)
                    for i in range(N):
                        if i <= NL - 1:
                            pf[i, s] = 0
                        elif i > NL - 1 and i <= mg[s, 0] - 1:
                            pf[i, s] = ldf[int(mg[s, 0]) - i - 1]
                        else:
                            pf[i, s] = vdf[i - int(mg[s, 0])]

            pf[:NL, :] = pf[:NL, :] / pf[:NL, :].sum(axis=0)
            pf[NL:N, :] = pf[NL:N, :] / pf[NL:N, :].sum(axis=0)
            pf = np.maximum(pf, 0)
            pf = np.nan_to_num(pf)

            Ts[j, :] = np.matmul(T[j, :], pf)
            Ps[j, :] = np.matmul(P[j, :], pf)

            xtemp = np.transpose(x, (1,2,0))
            xtemp = xtemp[:,:,j]
            xs[j,:,:] = np.matmul(xtemp, pf)

        ### For plotting
        self.t = t
        self.T = T
        self.PV = PV
        self.h = h
        self.nlist = [i + 1 for i in range(N)]  ## Because counting starts from 0.
        self.wsqN = wsq[:, NL - 1]
        self.NL = NL
        self.xc = xc
        self.T_I = T_I
        self.VF = VF
        self.Tl_avg = Tl_avg
        self.Tv_avg = Tv_avg
        if F > 0:
            self.VFV = VFV
        self.xl = xl
        self.xv = xv
        self.Ts = Ts
        self.Ps = Ps
        self.P = P
        self.Ts = Ts
        self.Ps = Ps
        self.xs = xs
        self.S = S
        print("Ready to Plot.")

    def plot_pressure(self):
        fig, ax = plt.subplots(1, 1, dpi=100)
        t = self.t * 24 * 60
        ax.plot(t, self.PV)
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        ax.minorticks_on()
        ax.set_xlim(xmin=0)
        ax.set_xlabel('Time (min)', fontname="Arial", fontsize=14)
        ax.set_ylabel('Pressure (kPa)', fontname="Arial", fontsize=14)
        ax.set_title('Pressure Profile', fontname="Arial", fontsize=16)
        for tick in ax.get_xticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        for tick in ax.get_yticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        return fig
    
    def plot_liquid_level(self):
        t = self.t * 24 * 60
        fig, ax = plt.subplots(1, 1, dpi=100)
        ax.plot(t, self.h)
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

        ax.minorticks_on()
        ax.set_xlim(xmin=0)
        ax.set_xlabel('Time (min)', fontname="Arial", fontsize=14)
        ax.set_ylabel('Liquid level (m)', fontname="Arial", fontsize=14)
        ax.set_title('Liquid Level Profile', fontname="Arial", fontsize=16)
        for tick in ax.get_xticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        for tick in ax.get_yticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        return fig

    def plot_temperature(self):
        t = self.t * 24 * 60
        fig, ax = plt.subplots(1, 1, dpi=100)
        ax.plot(t, self.Tl_avg)
        ax.plot(t, self.T_I)

        legend = ['Avg. Liquid Temperature', 'Interface Temperature']

        for i in range(self.NL,self.N):
            ax.plot(t, self.T[:, i])
            legend.append('Disk {} Temperature'.format(str(i+1)))

        ax.legend(legend)
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        ax.minorticks_on()
        ax.set_xlim(xmin=0)
        ax.set_xlabel('Time (min)', fontname="Arial", fontsize=14)
        ax.set_ylabel('Temperature (K)', fontname="Arial", fontsize=14)
        ax.set_title('Temperature Profiles', fontname="Arial", fontsize=16)
        for tick in ax.get_xticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        for tick in ax.get_yticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        return fig

    def plot_vapor_flows(self):
        t2 = [self.t[i,0] * 24 * 60 for i in range(len(self.t))]
        fig, ax = plt.subplots(1, 1, dpi=100)
        ax.plot(t2, self.wsqN)
        ax.plot(t2, self.VF)
        ax.legend(['Net Evaporation Rate', 'Net Vapour Addition Rate'])
        if self.F > 0:
            ax.plot(t2, self.VFV)
            ax.legend(['Net Evaporation Rate', 'Net Vapour Addition Rate', 'Feed Vapour Addition Rate'])
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

        ax.minorticks_on()
        ax.set_xlim(xmin=0)
        ax.set_xlabel('Time (min)', fontname="Arial", fontsize=14)
        ax.set_ylabel('Rate (kg/s)', fontname="Arial", fontsize=14)
        ax.set_title('Vapour Flows', fontname="Arial", fontsize=16)
        for tick in ax.get_xticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        for tick in ax.get_yticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        return fig

    def plot_liquid_compositions(self):
        t = self.t.reshape(1,-1)[0]
        t = t * 24 * 60
        fig, ax = plt.subplots(1, 1, dpi=100)
        for i in range(self.I):
            ax.plot(t, self.xl[:,i])

        legend = ['Component {}'.format(str(i+1)) for i in range(self.I)]
        ax.legend(legend)

        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

        ax.minorticks_on()
        ax.set_xlim(xmin=0)
        ax.set_xlabel('Time (min)', fontname="Arial", fontsize=14)
        ax.set_ylabel('Component Mass Fraction', fontname="Arial", fontsize=14)
        ax.set_title('Average Liquid Composition', fontname="Arial", fontsize=16)
        for tick in ax.get_xticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        for tick in ax.get_yticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        return fig

    def plot_vapor_compositions(self):
        t = self.t.reshape(1, -1)[0]
        t = t * 24 * 60
        fig, ax = plt.subplots(1, 1, dpi=100)
        for i in range(self.I):
            ax.plot(t, self.xv[:, i])

        legend = ['Component {}'.format(str(i + 1)) for i in range(self.I)]
        ax.legend(legend)

        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

        ax.minorticks_on()
        ax.set_xlim(xmin=0)
        ax.set_xlabel('Time (min)', fontname="Arial", fontsize=14)
        ax.set_ylabel('Component Mass Fraction', fontname="Arial", fontsize=14)
        ax.set_title('Average Vapour Composition', fontname="Arial", fontsize=16)
        for tick in ax.get_xticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        for tick in ax.get_yticklabels():
            tick.set_fontname("Arial")
            tick.set_fontsize(12)
        return fig

    def plot_product_temperature(self):
        fig, ax = plt.subplots(1, 1, dpi=100)
        if self.S > 0:
            t2 = [self.t[i,0] * 24 * 60 for i in range(len(self.t))]            
            ax.plot(t2, self.Ts)
            legend = ['Product {} Temperature'.format(str(i+1)) for i in range(len(self.Ts[1]))]
            ax.legend(legend)
            ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
            ax.minorticks_on()
            ax.set_xlim(xmin=0)
            ax.set_xlabel('Time (min)', fontname="Arial", fontsize=14)
            ax.set_ylabel('Temperature (K)', fontname="Arial", fontsize=14)
            ax.set_title('Product Temperature', fontname="Arial", fontsize=16)
            for tick in ax.get_xticklabels():
                tick.set_fontname("Arial")
                tick.set_fontsize(12)
            for tick in ax.get_yticklabels():
                tick.set_fontname("Arial")
                tick.set_fontsize(12)
        return fig

    def plot_product_pressure(self):
        fig, ax = plt.subplots(1, 1, dpi=100)
        if self.S > 0:
            t2 = [self.t[i, 0] * 24 * 60 for i in range(len(self.t))]
            ax.plot(t2, self.Ps)
            legend = ['Product {} Pressure'.format(str(i + 1)) for i in range(len(self.Ts[1]))]
            ax.legend(legend)
            ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
            ax.minorticks_on()
            ax.set_xlim(xmin=0)
            ax.set_xlabel('Time (min)', fontname="Arial", fontsize=14)
            ax.set_ylabel('Pressure (kPa)', fontname="Arial", fontsize=14)
            ax.set_title('Product Pressure', fontname="Arial", fontsize=16)
            for tick in ax.get_xticklabels():
                tick.set_fontname("Arial")
                tick.set_fontsize(12)
            for tick in ax.get_yticklabels():
                tick.set_fontname("Arial")
                tick.set_fontsize(12)
        return fig
    
    def save_results(self):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={"options":{'in_memory': True}})

        time = np.array(self.t * 24 * 60)
        diskName = ["Time (min)"] +["Disk {}".format(str(i+1)) for i in range(self.noDisks)]
        df = pd.DataFrame(columns=diskName, data=np.hstack([time, self.T]))
        df.to_excel(writer, sheet_name="Disk Temperature",index=False)

        df = pd.DataFrame(columns=["Time (min)", "h (m)"], data=np.hstack([time, self.h.reshape(-1,1)]))
        df.to_excel(writer, sheet_name="Liquid Level",index=False)

        columnName = ["Time (min)"] + [f"Disk {i} Component {j}" for i in range(1,self.noDisks+1) for j in range(1,self.noComponents+1)]
        df = pd.DataFrame(columns=columnName, data=np.hstack([time,self.xc]))
        df.to_excel(writer, sheet_name="Disk Composition",index=False)

        df = pd.DataFrame(columns=["Time (min)", "Temperature (K)"], data=np.hstack([time, self.T_I.reshape(-1,1)]))
        df.to_excel(writer, sheet_name="Interface Temperature",index=False)

        df = pd.DataFrame(columns=["Time (min)", "Pressure (kPa)"], data=np.hstack([time, self.PV.reshape(-1,1)]))
        df.to_excel(writer, sheet_name="Tank Pressure",index=False)

        df = pd.DataFrame(columns=["Time (min)", "Evaporation/Condensation Rate (kg/s)"], data=np.hstack([time, self.wsqN.reshape(-1,1)]))
        df.to_excel(writer, sheet_name="wsq",index=False)

        df = pd.DataFrame(columns=["Time (min)", "Net Vapour Addition Rate (kg/s)"], data=np.hstack([time, self.VF.reshape(-1,1)]))
        df.to_excel(writer, sheet_name="VF",index=False)

        df = pd.DataFrame(columns=diskName, data=np.hstack([time, self.P]))
        df.to_excel(writer, sheet_name="Disk Pressure",index=False)

        productName = ["Time (min)"] +["Product {}".format(str(i+1)) for i in range(self.noProductStreams)]
        df = pd.DataFrame(columns=productName, data=np.hstack([time, self.Ts]))
        df.to_excel(writer, sheet_name="Product Temperature",index=False)
        
        df = pd.DataFrame(columns=productName, data=np.hstack([time, self.Ps]))
        df.to_excel(writer, sheet_name="Product Pressure",index=False)

        columnName = ["Time (min)"] + [f"Product {i} Component {j}" for i in range(1,self.noProductStreams+1) for j in range(1,self.noComponents+1)]
        xs_data = np.hstack([self.xs[:,:,i] for i in range(self.S)])
        df = pd.DataFrame(columns=columnName, data=np.hstack([time,xs_data]))
        df.to_excel(writer, sheet_name="Product Composition",index=False)
        writer.close()

        return output
    