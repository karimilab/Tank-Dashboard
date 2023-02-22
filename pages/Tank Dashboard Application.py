import streamlit as st
import pandas as pd
from Tank_Damien import Tank
from datetime import datetime
import streamlit_ext as ste
from io import BytesIO
import os

st.set_page_config(page_title="Tank Dashboard", layout="centered")
st.title("Tank Dashboard")
tab1, tab2, tab3, tab4, tab5, tab6= st.tabs(["Components","Initial Conditions", "Streams", "Heat Leak", "Solver Settings", "Results"])

if not os.path.exists("temp"):
    os.makedirs("temp")

with st.form("my_form"):
    feeds = {}
    products = {}
    molecular_weights = {}
    molecule_dict = {'Ethane':16.0, 'Methane':30.0, 'Propane':44.1, 'Nitrogen':28.0, 'Hydrogen':2.0}

    with tab1:
        noComponents = st.selectbox("Number of components", range(1,6), index=3)
        componentList = ["" for i in range(noComponents)]
        uploaded_ModelF_file = st.file_uploader("Upload ModelF.py here", type="py")
        if uploaded_ModelF_file is not None:
            with open("temp\\ModelF.py", "wb") as outfile:
                outfile.write(uploaded_ModelF_file.getbuffer())
            ModelF = "temp.ModelF"
        else:
            ModelF = "neuralNetwork.ModelF"
        uploaded_ModelZg_file = st.file_uploader("Upload ModelZg.py here", type="py")
        if uploaded_ModelZg_file is not None:
            with open("temp\\ModelZg.py", "wb") as outfile:
                outfile.write(uploaded_ModelZg_file.getbuffer())
            ModelZg = "temp.ModelZg"
        else:
            ModelF = "neuralNetwork.ModelZg"
        componentHeader = [f"Component {i+1}" for i in range(noComponents)]
        for i in range(noComponents):
            st.subheader(f"Component {i+1}")
            componentName = st.selectbox("Name of component", list(molecule_dict.keys())+["Other"], key=f"componentName{i}")
            if componentName != "Other":
                st.write("Input complete. No additional input required for this component.")
                componentList[i] = f"components.{componentName}"
                molecular_weights[i+1] = molecule_dict[componentName]
            else:
                st.write("Please upload python file with functions")
                with open("components\\Component.py", "rb") as file:
                    ste.download_button("Download template python file here", file, f"Component{i+1}.py")
                uploaded_comp_file = st.file_uploader(f"Upload Component{i+1}.py here", type="py")
                if uploaded_comp_file is not None:
                    with open(f"temp\\Component{i+1}.py", "wb") as outfile:
                        outfile.write(uploaded_comp_file.getbuffer())
                componentList[i] = f"temp.Component{i+1}"

    with tab2:
        col1, col2 = st.columns([1,2])
        with col1:
            initialPressure = st.number_input("Initial Pressure (kPa)", value=110.0)
            tankDiameter = st.number_input("Tank Diameter (m)", value=63.0)
            tankHeight = st.number_input("Tank Height (m)", value=63.0)
            initialLiquidHeight = st.number_input("Initial liquid height (%)", min_value=0.0, max_value=100.0, value=90.0)
            st.subheader("Optional inputs")
            jacketStartValue = st.number_input("Jacket Start Point (%)", min_value=0.0, max_value=100.0)
            jacketEndValue = st.number_input("Jacket End Point (%)", min_value=0.0, max_value=100.0)
        with col2:
            st.image('tank.png')
        col1, col2 = st.columns(2)
        LDisks = {}
        Vdisks = {}
        noLDisks = 5
        noVDisks = 5
        columnNames = ["Disk Number", "Temperature (K)"] + [f"Component {i}" for i in range(1,noComponents+1)]
        st.subheader("Disk Intital Conditions: Please download template and upload file")
        st.caption("Component columns are in terms of mol fraction")
        with col1:
            noLDisks = st.number_input("Number of Liquid Disks:", value=5)
        with col2:
            noVDisks = st.number_input("Number of Vapour Disks:", value=5)

        def write_diskInit_file():
            diskTable = pd.DataFrame(columns=columnNames, dtype=float)
            rows = [f"Liquid Disk {i}" for i in range(1,noLDisks+1)] + [f"Vapour Disk {i}" for i in range(1,noVDisks+1)]
            temps = [113.0 for _ in range(noLDisks+noVDisks)]
            diskTable["Disk Number"] = rows
            diskTable["Temperature (K)"] = temps
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={"options":{'in_memory': True}})
            diskTable.to_excel(writer, index=False)
            writer.close()
            return output
        ste.download_button("Download template here", data=write_diskInit_file(), file_name="Disk Initial Conditions.xlsx")

        uploaded_initConditions_file = st.file_uploader("Upload Disk Initial Conditions here.")
        if uploaded_initConditions_file is not None:
            diskinitCombined = pd.read_excel(uploaded_initConditions_file)

    with tab3:
        col1, col2 = st.columns(2)
        with col1:
            noFeedStreams = st.selectbox("Number of feed streams", range(1,6), index=2)
        with col2:
            noProductStreams = st.selectbox("Number of product streams", range(1,6), index=2)
        st.write("Please input feed and product stream data by downloading the template and uploading the completed file.")
        feedColumnNames = ["Time (min)", "Flow rate (kg/s)", "Temperature (K)", "Pressure (kPa)"] + [f"Mass Frac {i}" for i in range(1,noComponents+1)]
        productColumnNames = ["Time (min)", "Flow rate (kg/s)"]

        def write_input_file():
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={"options":{'in_memory': True}})
            for i in range(1,noFeedStreams+1):
                df = pd.DataFrame(columns=feedColumnNames)
                df.to_excel(writer, sheet_name=f"Feed {i}",index=False)  
            for i in range(1,noProductStreams+1):
                df = pd.DataFrame(columns=productColumnNames)
                df.to_excel(writer, sheet_name=f"Product {i}",index=False) 
            writer.close()
            return output

        ste.download_button("Download template here", data=write_input_file(), file_name="feed_product_data.xlsx")
        uploaded_input_file = st.file_uploader("Upload completed data here")
        if uploaded_input_file is not None:
            feed_product_df = pd.read_excel(uploaded_input_file,sheet_name=None)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            for i in range(1,noFeedStreams+1):
                st.image('Arrow.png')
                feeds[i] = st.number_input(f"Feed {i} Height (%)", min_value=0.0, max_value=100.0, key=f"feed{i}", value=95.0)
        with col2:
            st.image('tank.png')
        with col3:
            for i in range(1,noProductStreams+1):
                st.image('Arrow.png')
                products[i] = st.number_input(f"Product {i} Height (%)", min_value=0.0, max_value=100.0, key=f"product{i}", value=100.0)

    with tab4:
        sigma = st.number_input("Evaporation/Condensation Coefficient ((kmol/kg)\u2070\u0387\u2075.s.m\u207b\u00b9):", format="%e", value=5e-09, min_value=0.0)
        Ul = st.number_input("Liquid Phase Film Heat Transfer Coefficient (W/(m\u00b2.K)):", format="%.2f", value=200.0, min_value=0.0)
        Uv = st.number_input("Vapour Phase Film Heat Transfer Coefficient (W/(m\u00b2.K)):", format="%.2f",value=10.0, min_value=0.0)
        Uvw = st.number_input("Wall-Vapour Heat Transfer Coefficient (W/(m\u00b2.K)):", format="%.3f",value=0.02, min_value=0.0)
        Ulw = st.number_input("Wall-Liquid Heat Transfer Coefficient (W/(m\u00b2.K)):", format="%.3f",value=0.02, min_value=0.0)
        Ur = st.number_input("Tank Roof-Vapour Heat Transfer Coefficient (W/(m\u00b2.K)):", format="%.3f",value=0.025, min_value=0.0)
        Ub = st.number_input("Tank Bottom-Liquid Heat Transfer Coefficient (W/(m\u00b2.K)):", format="%.3f",value=0.025, min_value=0.0)
        Uvr = st.number_input("Jacket-Vapour Heat Transfer Coefficient (W/(m\u00b2.K)):", format="%.3f",value=0.02, min_value=0.0)
        Ulr = st.number_input("Jacket-Liquid Heat Transfer Coefficient (W/(m\u00b2.K)):", format="%.3f",value=0.02, min_value=0.0)
        groundTemp = st.number_input("Ground Temperature (K):",value=298.0, min_value=0.0)
        ambTemp = st.number_input("Ambient Temperature (K):",value=298.0, min_value=0.0)
        roofTemp = st.number_input("Roof Temperature (K):",value=298.0, min_value=0.0)
        refridgeTemp = st.number_input("Refrigerant Temperature (K):",value=93.0, min_value=0.0)

    with tab5:
        abstol = st.number_input("Absolute DAE Solver Tolerance:",value=0.01, min_value=0.0, max_value=1.0)
        reltol = st.number_input("Relative DAE Solver Tolerance:", format="%.4f",value=0.0001, min_value=0.0, max_value=1.0)
        numberofIterations = st.number_input("Running Time (min):",value=40,step=5)
    
    simulation_ran = st.form_submit_button('Run simulation')


    if simulation_ran:
        if uploaded_input_file is None:
            st.error("Please upload feed flows")
            st.stop()
        if uploaded_initConditions_file is None:
            st.error("Please upload initial conditions")
            st.stop()
        myTank = Tank(noFeedStreams, noProductStreams, tankDiameter, tankHeight, initialPressure, 
            initialLiquidHeight, feeds, products, feed_product_df,
            noComponents, molecular_weights, componentList,  
            jacketStartValue, jacketEndValue, sigma, Ul,
            Uv, Uvw, Ulw, Ur, Ub, Uvr, Ulr, groundTemp, ambTemp, roofTemp, refridgeTemp, 
            noLDisks, noVDisks, abstol, reltol, numberofIterations, diskinitCombined)
        checkStatus = myTank.check_input()
        if checkStatus is not True:
            st.error(checkStatus, icon="🚨")
            st.stop()
        with st.spinner(text="Pre-processing data..."):
            myTank.data_preprocessing()
        with st.spinner(text="Running Simulation..."):
            myTank.run_simulation()
            st.success("Simulation completed. Please check results tab.")
            st.session_state.submitted = True
            st.session_state.Tank = myTank

    with tab6:
        if 'submitted' in st.session_state:
            myTank = st.session_state.Tank
            now = datetime.now()
            current_time = now.strftime("%d-%m-%Y %H%M")
            nameResultsExcel = f"Results {current_time}.xlsx"
            ste.download_button("Download Results here", data=myTank.save_results(), file_name=nameResultsExcel)
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["Pressure", "Liquid Level", 
                "Temperature", "Vapor Flows", "Liquid Comp", "Vapor Comp", "Product Temp", "Product Pressure"])
            
            with tab1:
                fig = myTank.plot_pressure()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                ste.download_button("Download Figure here", data=byte_im, file_name="Pressure.png",mime="image/png")
            with tab2:
                fig = myTank.plot_liquid_level()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                ste.download_button("Download Figure here", data=byte_im, file_name="Liquid Level.png",mime="image/png")
            with tab3:
                fig = myTank.plot_temperature()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                ste.download_button("Download Figure here", data=byte_im, file_name="Temperature Profiles.png",mime="image/png")
            with tab4:
                fig = myTank.plot_vapor_flows()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                ste.download_button("Download Figure here", data=byte_im, file_name="Vapor Flows.png",mime="image/png")
            with tab5:
                fig = myTank.plot_liquid_compositions()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                ste.download_button("Download Figure here", data=byte_im, file_name="Liquid Compositions.png",mime="image/png")
            with tab6:
                fig = myTank.plot_vapor_compositions()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                ste.download_button("Download Figure here", data=byte_im, file_name="Vapor Compositions.png",mime="image/png")
            with tab7:
                fig = myTank.plot_product_temperature()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                ste.download_button("Download Figure here", data=byte_im, file_name="Product Temperature.png",mime="image/png")
            with tab8:
                fig = myTank.plot_product_pressure()
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format='png', dpi=500, bbox_inches="tight")
                byte_im = buf.getvalue()
                ste.download_button("Download Figure here", data=byte_im, file_name="Product Pressure.png",mime="image/png")
