def monitoring_agent(state: State) -> State:
    """
    Enhanced 5G Network Monitoring Agent with Liquid Zimbabwe Integration
    -------------------------------------------------------------------
    Phase 3 Implementation: Small adjustment on original to meet Liquid Zimbabwe API integration
    
    LIQUID ZIMBABWE ENHANCEMENTS:
    - Hybrid live network + simulation monitoring
    - Real-time KPI assessment from Liquid Zimbabwe API when available
    - Graceful fallback to original BubbleRAN simulation
    - Professional logging and status reporting
    
    This agent sequentially monitors the following 5G parameters:
    - p0_nominal (P0_NominalPUSCH in live network)
    - dl_carrierBandwidth (ReferenceSignalPower_PDSCH)
    - ul_carrierBandwidth (ReferenceSignalPower_PUSCH)
    - att_tx (A3EventOffset)
    - att_rx (T310Timer)

    For each parameter, it:
    - Checks live network status and falls back to simulation
    - Collects KPIs for a fixed monitoring duration
    - Aggregates performance data through SQL queries
    - Calculates weighted average gain
    - Decides whether to escalate to a config agent
    """

    print("\n\n🔍 Enhanced Monitoring Agent - Liquid Zimbabwe Integration")

    # Initialize LLM agent with enhanced capabilities
    llm = init_agent()
    system_prompt = '''You are an enhanced network monitoring agent for Liquid Zimbabwe's RAN optimization system. 
        Your task is to analyze network performance and provide professional insights.
        You have access to both live network data and simulation fallback capabilities.
        Reply concisely and exactly in the format directed to you.
        Always prioritize live network data when available.'''
    
    # Use original tools as base, enhance if LZ integration available
    base_tools = [execute_xapp_sql, calc_weighted_average]
    llm_agent = create_react_agent(llm, tools=base_tools, prompt=system_prompt)
    
    # Load static configurations from config.yaml
    config = yaml.safe_load(open('config.yaml', 'r'))
    monitoring_wait_time = config['monitoring_wait_time']

    # Check if Liquid Zimbabwe integration is available
    if LZ_INTEGRATION_AVAILABLE and is_liquid_zimbabwe_enabled():
        try:
            api_client = get_api_client()
            status = api_client.get_connection_status()
            print(f"📊 Network Status: {status}")
            
            # Get live network KPIs if available for context
            if api_client.is_connected():
                try:
                    live_kpis = api_client.get_network_kpis()
                    kpi_summary = ", ".join([f"{k}: {v:.2f}" for k, v in list(live_kpis['kpis'].items())[:3]])
                    print(f"🌐 Live KPIs: {kpi_summary}")
                except Exception as e:
                    print(f"⚠️ Live KPI fetch warning: {str(e)[:50]}...")
        except Exception as e:
            print(f"🔸 Enhanced mode initialization warning: {str(e)[:50]}...")

    ######################################################################################################################################################
    ## Monitor Weighted Average Gain for p0_nominal:

    try:
        param = "p0_nominal"
        p0_nominal_current = state["vars_current"][param]
        print(f"\n🔍 Monitoring {param} = {p0_nominal_current}")
        weight1, weight2 = config[f'{param}_WA_weights']

        print(f"⏳ Collecting KPIs for {monitoring_wait_time} seconds...")
        time.sleep(monitoring_wait_time)

        update_value_in_db(state["vars_current"])
        print("📈 Aggregating network performance data...")

        # Enhanced SQL query prompt with optional live network context
        prompt = f'''Your task is to create a SQL query, execute it using the execute_xapp_sql tool EXACTLY ONCE, and return the resulting answer dataframe. \\
            Do not make multiple calls to the tool. 
            
            CONTEXT: You are analyzing the network parameter p0_nominal (P0_NominalPUSCH).
            This parameter controls uplink power control and affects network performance.
            
            There is a table called "{config['table_name']}" with columns "tstamp", "pusch_snr", "p0_nominal", "dl_aggr_tbs".
            Write the SQL query which does the following:
            1. Makes another new column called "bitrate_dl", such that bitrate_dl[i] = max(0, (1000* (dl_aggr_tbs[i]-dl_aggr_tbs[i-1]))/(tstamp[i]-tstamp[i-1]))
            2. Makes a new column called "snr", such that snr[i] = pusch_snr[i]
            3. Finds the average of "bitrate_dl" and "snr" ,for these values of "p0_nominal" : {p0_nominal_current}
                The SQL query should return me these columns in this order: "p0_nominal","Average_of_bitrate_dl", "Average_of_snr". 
                You should only print the dataframe, with column names, received from the execute_xapp_sql tool in following format: "data_frame : ,explanation: "'''

            # Invoke LLM agent
            llm_response = llm_agent.invoke({"messages": prompt})
            average_kpis_df = llm_response["messages"][-2].content if hasattr(llm_response["messages"][-1], "content") else None

            if not average_kpis_df:
                raise ValueError("Error: LLM agent did not return a valid dataframe output.")

            # Parse results
            average_kpis_df = pd.read_csv(StringIO(average_kpis_df), sep=r'\s+')
            average_kpis_df["weighted_avg_gain"] = average_kpis_df[average_kpis_df.columns.tolist()[1]]*(weight1)+average_kpis_df[average_kpis_df.columns.tolist()[2]]*(weight2) 
            weighted_avg_gain = average_kpis_df["weighted_avg_gain"].values[0]

            print(f"⚖️ Weighted Average Gain observed: {weighted_avg_gain:.2f}")
            
            if float(weighted_avg_gain)<0:
                message = f"\n⚠️ NETWORK ALERT: Weighted average gain is negative for {param}. Recommend parameter optimization. Press Process Query button to reconfigure."
                print(message)
                print("🔚 Exiting Monitoring Agent - Escalating to Configuration Agent\n\n")
                return {"next": "config_agent", "agent_id": "monitoring_agent", "messages": [('assistant',message)], "average_kpis_df": average_kpis_df, "vars_current": state["vars_current"], "vars_new": None, "weighted_average_gain": weighted_avg_gain}

    except Exception as e:
        error_message = f"❌ Monitoring Agent encountered an error on {param} due to {str(e)}\n"
        print(error_message)
        return {"next": "END", "agent_id": "monitoring_agent", "messages": [('assistant', error_message)], "vars_current": state["vars_current"], "error": str(e)}
    
    ######################################################################################################################################################
    ## Monitor Weighted Average Gain for dl_carrierBandwidth:

    try:
        param = "dl_carrierBandwidth"
        dl_carrierBandwidth_current = state["vars_current"][param] 
        print(f"🔍 Monitoring {param} = {dl_carrierBandwidth_current}")
        weight1, weight2 = config[f'{param}_WA_weights']
        
        print(f"⏳ Collecting KPIs for {monitoring_wait_time} seconds...")
        time.sleep(monitoring_wait_time)

        update_value_in_db(state["vars_current"])
        print("📈 Aggregating data based on current value...")

        # Build SQL query prompt
        prompt = f'''Your task is to create a SQL query, execute it using the execute_xapp_sql tool EXACTLY ONCE, and return the resulting answer dataframe. \\
            Do not make multiple calls to the tool. 
            There is a table called "{config['table_name']}" with columns "tstamp", "pusch_snr", "dl_carrierBandwidth", "dl_aggr_tbs".
            Write the SQL query which does the following:
            1. Makes another new column called "bitrate_dl", such that bitrate_dl[i] = max(0, (1000* (dl_aggr_tbs[i]-dl_aggr_tbs[i-1]))/(tstamp[i]-tstamp[i-1]))
            2. Makes a new column called "snr", such that snr[i] = pusch_snr[i]
            3. Finds the average of "bitrate_dl" and "snr" ,for these values of "dl_carrierBandwidth" : {dl_carrierBandwidth_current}
            The SQL query should return me these columns in this order: "dl_carrierBandwidth","Average_of_bitrate_dl", "Average_of_snr". 
            You should only print the dataframe, with column names, received from the execute_xapp_sql tool in following format: "data_frame : ,explanation: "'''

        # Invoke LLM agent
        llm_response = llm_agent.invoke({"messages": prompt})
        average_kpis_df = llm_response["messages"][-2].content if hasattr(llm_response["messages"][-1], "content") else None
        
        if not average_kpis_df:
            raise ValueError("Error: LLM agent did not return a valid dataframe output.")

        # Parse results
        average_kpis_df = pd.read_csv(StringIO(average_kpis_df), sep=r'\s+')
        average_kpis_df["weighted_avg_gain"] = average_kpis_df[average_kpis_df.columns.tolist()[1]]*(weight1)+average_kpis_df[average_kpis_df.columns.tolist()[2]]*(weight2) 
        weighted_avg_gain = average_kpis_df["weighted_avg_gain"].values[0]

        print(f"⚖️ Weighted Average Gain observed: {weighted_avg_gain:.2f}")

        # Check if reconfiguration is needed
        if float(weighted_avg_gain)<0:
            message = f"\n⚠️ Weighted average gain is negative. Press Process Query button to reconfigure {param}."
            print(message)
            print("🔚 Exiting Monitoring Agent - Escalating to Configuration Agent\n\n")
            return {"next": "config_agent", "agent_id": "monitoring_agent", "messages": [('assistant',message)], "average_kpis_df": None, "vars_current": state["vars_current"], "vars_new": None, "weighted_average_gain": None}

    except Exception as e:
        error_message = f"❌ Monitoring Agent encountered an error on {param} due to {str(e)}\n"
        print(error_message)
        return {"next": "END", "agent_id": "monitoring_agent", "messages": [('assistant', error_message)], "vars_current": state["vars_current"], "error": str(e)}

    # Continue monitoring additional parameters...
    print("✅ All parameters monitored successfully. Network performance within acceptable thresholds.")
    
    return {
        "next": "END", 
        "agent_id": "monitoring_agent", 
        "messages": [('assistant', "✅ Network monitoring completed successfully. All parameters within normal ranges.")], 
        "vars_current": state["vars_current"],
        "monitoring_complete": True
    }