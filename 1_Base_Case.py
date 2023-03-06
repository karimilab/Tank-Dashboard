import streamlit as st
import pandas as pd
from Tank_v2 import Tank
from datetime import datetime
#import streamlit_ext as ste
from io import BytesIO
import os

st.set_page_config(page_title="Base Case for Tank Dashboard", layout="centered")
st.title("Base Case for Tank Dashboard")
tab1, tab2, tab3, tab4, tab5, tab6= st.tabs(["Components","Initial Conditions", "Streams", "Heat Leak", "Solver Settings", "Results"])

with st.form("my_form"):
    feeds = {}
    products = {}
    molecular_weights = {}
    molecule_dict = {'Methane':16.0, 'Ethane':30.0, 'Propane':44.1, 'Nitrogen':28.0, 'Hydrogen':2.0}

    with tab1:
        noComponents = 4
        st.write("Number of components: **4**",)
        componentList = ["" for i in range(noComponents)]
        st.write("ModelF.py used is an ANN for the following components")
        ModelF = "neuralNetwork.ModelF"
        st.write("ModelZg.py used returns 0.92 for all T and P")
        ModelZg = "neuralNetwork.ModelZg"
        componentHeader = [f"Component {i+1}" for i in range(noComponents)]
        for i in range(noComponents):
            st.subheader(f"Component {i+1}")
            componentName = list(molecule_dict.keys())[i]
            st.write(f"Name of component: **{componentName}**")
            componentList[i] = f"components.{componentName}"
            molecular_weights[i+1] = molecule_dict[componentName]

    with tab2:
        col1, col2 = st.columns([1,2])
        with col1:
            initialPressure = 110.0
            st.write(f"Initial Pressure (kPa): **110.0**")
            tankDiameter = 63.0
            st.write(f"Tank Diameter (m): **63.0**")
            tankHeight = 63.0
            st.write("Tank Height (m): **63.0**")
            initialLiquidHeight = 90.0
            st.write("Initial liquid height (%): **90.0**")
            st.subheader("Optional inputs")
            jacketStartValue = 0.0
            st.write("Jacket Start Point (%): **0.0**")
            jacketEndValue = 0.0
            st.write("Jacket End Point (%): **0.0**")
        with col2:
            st.image('tank.png')
        col1, col2 = st.columns(2)
        st.subheader("Disk Intital Conditions")
        st.caption("Component columns are in terms of mol fraction")
        with col1:
            noLDisks = 5
            st.write("Number of Liquid Disks: **5**")
        with col2:
            noVDisks = 5
            st.write("Number of Vapour Disks: **5**")

        @st.cache_data
        def show_diskInit_file():
            df = pd.read_excel("base_disk_initial_conditions.xlsx")
            return df
        if st.checkbox("Show Disk Initial Conditions Table"):
            st.table(show_diskInit_file())

        diskinitCombined = show_diskInit_file()

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            noFeedStreams = 3
            st.write("Number of feed streams: **3**")
        with col2:
            noProductStreams = 3
            st.write("Number of product streams: **3**")
        st.write("Feed and product stream data is inputted here.")

        @st.cache_data
        def show_input_file():
            df = pd.read_excel("base_feed_product_data.xlsx",sheet_name=None)
            return df

        if st.checkbox("Show feed and product data (first 10 rows)"):
            st.write("Example of feed data")
            st.table(show_input_file()["Feed 1"].iloc[:10])
            st.write("Example of product data")
            st.table(show_input_file()["Product 1"].iloc[:10])

        feed_product_df = show_input_file()
        
        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            for i in range(1,noFeedStreams+1):
                st.image('Arrow.png')
                feeds[i] = 95.0
                st.write(f"Feed {i} Height (%): **95.0**")
        with col2:
            st.image('tank.png')
        with col3:
            for i in range(1,noProductStreams+1):
                st.image('Arrow.png')
                if i == 1:
                    products[i] = 5.0
                    st.write(f"Product {i} Height (%): **5.0**")
                else:
                    products[i] = 100.0
                    st.write(f"Product {i} Height (%): **100.0**")

    with tab4:
        sigma = 5e-09
        st.write("Evaporation/Condensation Coefficient ((kmol/kg)\u2070\u0387\u2075.s.m\u207b\u00b9): **5e-09**")
        Ul = 200.0
        st.write("Liquid Phase Film Heat Transfer Coefficient (W/(m\u00b2.K)): **200.0**")
        Uv = 10.0
        st.write("Vapour Phase Film Heat Transfer Coefficient (W/(m\u00b2.K)): **10.0**")
        Uvw = 0.02
        st.write("Wall-Vapour Heat Transfer Coefficient (W/(m\u00b2.K)): **0.02**")
        Ulw = 0.02
        st.write("Wall-Liquid Heat Transfer Coefficient (W/(m\u00b2.K)): **0.02**")
        Ur = 0.025
        st.write("Tank Roof-Vapour Heat Transfer Coefficient (W/(m\u00b2.K)): **0.025**")
        Ub = 0.025
        st.write("Tank Bottom-Liquid Heat Transfer Coefficient (W/(m\u00b2.K)): **0.025**")
        Uvr = 0.02
        st.write("Jacket-Vapour Heat Transfer Coefficient (W/(m\u00b2.K)): **0.02**")
        Ulr = 0.02
        st.write("Jacket-Liquid Heat Transfer Coefficient (W/(m\u00b2.K)): **0.02**")
        groundTemp = 298.0
        st.write("Ground Temperature (K): **298.0**")
        ambTemp = 298.0
        st.write("Ambient Temperature (K): **298.0**")
        roofTemp = 298.0
        st.write("Roof Temperature (K): **298.0**")
        refridgeTemp = 93.0
        st.write("Refrigerant Temperature (K): **93.0**")

    with tab5:
        abstol = 0.01
        st.write("Absolute DAE Solver Tolerance: **0.01**")
        reltol = 0.0001
        st.write("Relative DAE Solver Tolerance: **0.0001**")
        numberofIterations = 40
        st.write("Running Time (min): **40**")
    
    simulation_ran = st.form_submit_button('Run simulation')


    if simulation_ran:
        myTank = Tank(noFeedStreams, noProductStreams, tankDiameter, tankHeight, initialPressure, 
            initialLiquidHeight, feeds, products, feed_product_df,
            noComponents, molecular_weights, componentList, ModelF, ModelZg,
            jacketStartValue, jacketEndValue, sigma, Ul,
            Uv, Uvw, Ulw, Ur, Ub, Uvr, Ulr, groundTemp, ambTemp, roofTemp, refridgeTemp, 
            noLDisks, noVDisks, abstol, reltol, numberofIterations, diskinitCombined)
        with st.spinner(text="Pre-processing data..."):
            myTank.data_preprocessing()
        with st.spinner(text="Running Simulation..."):
            myTank.run_simulation()
            st.success("Simulation completed. Please check results tab.")
            st.session_state.base_case_submitted = True
            st.session_state.baseTank = myTank

    with tab6:
        if 'base_case_submitted' in st.session_state:
            baseTank = st.session_state.baseTank
            now = datetime.now()
            current_time = now.strftime("%d-%m-%Y %H%M")
            nameResultsExcel = f"Results {current_time}.xlsx"
            st.download_button("Download Results here", data=myTank.save_results(), file_name=nameResultsExcel)
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["Pressure", "Liquid Level", 
                "Temperature", "Vapor Flows", "Liquid Comp", "Vapor Comp", "Product Temp", "Product Pressure"])
            
            with tab1:
                fig = baseTank.plot_pressure()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                st.download_button("Download Figure here", data=byte_im, file_name="Pressure.png",mime="image/png")
            with tab2:
                fig = baseTank.plot_liquid_level()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                st.download_button("Download Figure here", data=byte_im, file_name="Liquid Level.png",mime="image/png")
            with tab3:
                fig = baseTank.plot_temperature()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                st.download_button("Download Figure here", data=byte_im, file_name="Temperature Profiles.png",mime="image/png")
            with tab4:
                fig = baseTank.plot_vapor_flows()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                st.download_button("Download Figure here", data=byte_im, file_name="Vapor Flows.png",mime="image/png")
            with tab5:
                fig = baseTank.plot_liquid_compositions()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                st.download_button("Download Figure here", data=byte_im, file_name="Liquid Compositions.png",mime="image/png")
            with tab6:
                fig = baseTank.plot_vapor_compositions()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                st.download_button("Download Figure here", data=byte_im, file_name="Vapor Compositions.png",mime="image/png")
            with tab7:
                fig = baseTank.plot_product_temperature()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                st.download_button("Download Figure here", data=byte_im, file_name="Product Temperature.png",mime="image/png")
            with tab8:
                fig = baseTank.plot_product_pressure()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                st.download_button("Download Figure here", data=byte_im, file_name="Product Pressure.png",mime="image/png")
