"""
Phase 3: Small Adjustment on Original to Meet Liquid Zimbabwe API Integration
Based on the working template from bubbleran/Telco-Network-Configuration

PHASE 3 ENHANCEMENTS:
- Hybrid architecture combining live Liquid Zimbabwe API with BubbleRAN simulation
- Graceful fallback from live network to simulation
- Optional Liquid Zimbabwe KPI integration without breaking core functionality
- Maintains original 3-agent workflow with minimal modifications

This file implements the original 3-agent functionality:
- Configuration Agent: Analyzes queries and suggests parameter changes
- Validation Agent: Tests changes and validates improvements  
- Monitoring Agent: Continuously monitors network performance

Liquid Zimbabwe enhancements are added as optional features that don't break core functionality.
"""

import json
import sqlite3
import time
from copy import deepcopy
from io import StringIO
import os
import requests

import pandas as pd
import streamlit as st
import yaml
from pydantic import BaseModel
from typing import Annotated, Dict, Literal, Optional, Union
from typing_extensions import TypedDict

import langgraph
from langgraph.graph import END, MessagesState, StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
from langgraph.types import Command

from langchain_core.messages import AnyMessage, HumanMessage, convert_to_messages
from langchain_core.tools import tool
from langchain_nvidia_ai_endpoints import ChatNVIDIA

# Import original working tools
from agentic_llm_workflow.tools import (
    calc_weighted_average, 
    execute_historical_sql, 
    execute_xapp_sql, 
    find_value_in_gnb
)

from agentic_llm_workflow.utils import (
    check_network_status, 
    start_network, 
    stop_network, 
    update_value_in_db, 
    update_value_in_gnb
)

# Phase 3: Import Liquid Zimbabwe integration with graceful fallback
try:
    from agentic_llm_workflow.lz_config import LZ_CONFIG, is_liquid_zimbabwe_enabled
    from agentic_llm_workflow.lz_api_client import LiquidZimbabweAPIClient
    
    LZ_INTEGRATION_AVAILABLE = True
    _lz_api_client = None
    
    def get_api_client():
        global _lz_api_client
        if _lz_api_client is None:
            _lz_api_client = LiquidZimbabweAPIClient()
        return _lz_api_client
        
    print("✅ Phase 3: Liquid Zimbabwe integration loaded successfully")
    
except ImportError as e:
    LZ_INTEGRATION_AVAILABLE = False
    
    def is_liquid_zimbabwe_enabled():
        return False
        
    def get_api_client():
        return None
    
    print(f"🔸 Phase 3: Liquid Zimbabwe integration not available (fallback mode): {e}")
    print("   System will operate in pure BubbleRAN simulation mode")

# Optional: Try to import enhanced tools but don't fail if they're not available
try:
    from agentic_llm_workflow.enhanced_tools import (
        get_live_network_kpis,
        check_live_network_status,
        get_network_mode_status
    )
    ENHANCED_TOOLS_AVAILABLE = True
except ImportError:
    print("Enhanced tools not available - using standard tools only")
    ENHANCED_TOOLS_AVAILABLE = False


class State(TypedDict):
    """
    Defines the structure for maintaining state in the LangGraph workflow.
    """
    next: str
    agent_id: str  
    messages: Annotated[list, add_messages]
    average_kpis_df: Optional[pd.DataFrame]
    weighted_average_gain: Optional[pd.DataFrame]
    vars_current: Dict[str, int]  # Current parameter values
    vars_new: Dict[str, int]      # New parameter values


def init_agent():
    """
    Initializes the ChatNVIDIA agent based on runtime configuration.
    Returns: ChatNVIDIA instance
    """
    config = yaml.safe_load(open('config.yaml', 'r'))

    if not config['NIM_mode']:
        # Use API Catalog
        llm = ChatNVIDIA(
            model=config['llm_model'],
            api_key=config['nvidia_api_key'], 
            base_url=config['llm_base_url'],
            temperature=config['llm_temp'],
            top_p=config['llm_top_p'],
            max_tokens=config['llm_max_tokens'],
        )
    else: 
        # Use local NIM
        nim_image = config['nim_image']
        nim_llm_model = nim_image.split("nvcr.io/nim/")[-1].split(":")[0]
        nim_llm_port = config['nim_llm_port']
        
        if "BUBBLERAN_HOST_PWD" in os.environ:
            nim_base_url = f"http://host.docker.internal:{nim_llm_port}/v1"
        else:
            nim_base_url = f"http://localhost:{nim_llm_port}/v1"

        llm = ChatNVIDIA(
            model=nim_llm_model,
            api_key=config['nvidia_api_key'], 
            base_url=nim_base_url,
            temperature=config['llm_temp'],
            top_p=config['llm_top_p'],
            max_tokens=config['llm_max_tokens'],
        )
    return llm


def monitoring_agent(state: State) -> State:
    """
    Restored Original Monitoring Agent with Optional Liquid Zimbabwe Features
    
    This agent sequentially monitors 5 parameters:
    - p0_nominal, dl_carrierBandwidth, ul_carrierBandwidth, att_tx, att_rx
    
    For each parameter:
    - Collects KPIs for monitoring duration
    - Calculates weighted average gain
    - Escalates to config agent if performance degrades
    """
    
    print("\n\nInside Monitoring Agent")
    
    # Add optional Liquid Zimbabwe logging
    if ENHANCED_TOOLS_AVAILABLE:
        print("🔍 Enhanced Liquid Zimbabwe Monitoring Active")
        
        # Optional: Get network status if available
        try:
            mode_status = get_network_mode_status()
            yield f"📊 Network Mode: {mode_status}"
        except:
            pass

    # Initialize LLM agent with original tools
    llm = init_agent()
    system_prompt = 'You are an agent in a LangGraph. Your task is to help a user configure or analyze a current 5G network. Reply concisely and exactly in the format directed to you.'
    llm_agent = create_react_agent(llm, tools=[execute_xapp_sql, calc_weighted_average], prompt=system_prompt)
    
    config = yaml.safe_load(open('config.yaml', 'r'))
    monitoring_wait_time = config['monitoring_wait_time']

    # Monitor each parameter sequentially (original logic)
    for param in ["p0_nominal", "dl_carrierBandwidth", "ul_carrierBandwidth", "att_tx", "att_rx"]:
        try:
            param_current = state["vars_current"][param]
            yield f"Monitoring {param} = {param_current}: "
            weight1, weight2 = config[f'{param}_WA_weights']

            yield f"Collecting KPIs for {monitoring_wait_time} seconds..."
            time.sleep(monitoring_wait_time)

            update_value_in_db(state["vars_current"])
            yield "Aggregating data based on current value..."

            # Build SQL query based on parameter type
            if param == "p0_nominal":
                sql_columns = "tstamp", "pusch_snr", "p0_nominal", "dl_aggr_tbs"
                kpi1, kpi2 = "bitrate_dl", "snr"
                calculation = "bitrate_dl[i] = max(0, (1000* (dl_aggr_tbs[i]-dl_aggr_tbs[i-1]))/(tstamp[i]-tstamp[i-1]))"
                calculation2 = "snr[i] = pusch_snr[i]"
            
            elif param in ["dl_carrierBandwidth", "att_tx"]:
                sql_columns = "tstamp", "pusch_snr", param, "dl_aggr_tbs"  
                kpi1, kpi2 = "bitrate_dl", "snr"
                calculation = "bitrate_dl[i] = max(0, (1000* (dl_aggr_tbs[i]-dl_aggr_tbs[i-1]))/(tstamp[i]-tstamp[i-1]))"
                calculation2 = "snr[i] = pusch_snr[i]"
                
            elif param == "ul_carrierBandwidth":
                sql_columns = "tstamp", "dl_harq_round1", "dl_harq_round2", "dl_harq_round3", param, "ul_aggr_tbs"
                kpi1, kpi2 = "bitrate_ul", "retx" 
                calculation = "bitrate_ul[i] = max(0, (1000* (ul_aggr_tbs[i]-ul_aggr_tbs[i-1]))/(tstamp[i]-tstamp[i-1]))"
                calculation2 = "retx[i] = max(0, (1000*(dl_harq_round0[i] + dl_harq_round1[i] + dl_harq_round2[i] + dl_harq_round3[i] - dl_harq_round0[i-1] - dl_harq_round1[i-1] - dl_harq_round2[i-1] - dl_harq_round3[i-1] ))/ (tstamp[i]-tstamp[i-1]))"
                
            elif param == "att_rx":
                sql_columns = "tstamp", "dl_harq_round1", "dl_harq_round2", "dl_harq_round3", param, "ul_aggr_tbs"
                kpi1, kpi2 = "bitrate_ul", "retx"
                calculation = "bitrate_ul[i] = max(0, (1000* (ul_aggr_tbs[i]-ul_aggr_tbs[i-1]))/(tstamp[i]-tstamp[i-1]))"
                calculation2 = "retx[i] = max(0, (1000*(dl_harq_round0[i] + dl_harq_round1[i] + dl_harq_round2[i] + dl_harq_round3[i] - dl_harq_round0[i-1] - dl_harq_round1[i-1] - dl_harq_round2[i-1] - dl_harq_round3[i-1] ))/ (tstamp[i]-tstamp[i-1]))"

            # Create SQL prompt
            prompt = f'''Your task is to create a SQL query, execute it using the execute_xapp_sql tool EXACTLY ONCE, and return the resulting answer dataframe.
            Do not make multiple calls to the tool. 
            There is a table called "{config['table_name']}" with columns {sql_columns}.
            Write the SQL query which does the following:
            1. Makes another new column called "{kpi1}", such that {calculation}
            2. Makes a new column called "{kpi2}", such that {calculation2}  
            3. Finds the average of "{kpi1}" and "{kpi2}" for these values of "{param}": {param_current}
            The SQL query should return me these columns in this order: "{param}","Average_of_{kpi1}", "Average_of_{kpi2}". 
            You should only print the dataframe, with column names, received from the execute_xapp_sql tool in following format: "data_frame : ,explanation: "'''

            # Execute LLM query
            llm_response = llm_agent.invoke({"messages": prompt})
            average_kpis_df = llm_response["messages"][-2].content if hasattr(llm_response["messages"][-1], "content") else None
            
            if not average_kpis_df:
                raise ValueError("Error: LLM agent did not return a valid dataframe output.")

            # Calculate weighted average gain
            average_kpis_df = pd.read_csv(StringIO(average_kpis_df), sep=r'\s+')
            average_kpis_df["weighted_avg_gain"] = (average_kpis_df[average_kpis_df.columns.tolist()[1]] * weight1 + 
                                                   average_kpis_df[average_kpis_df.columns.tolist()[2]] * weight2)
            weighted_avg_gain = average_kpis_df["weighted_avg_gain"].values[0]

            yield f"Weighted Average Gain observed: {weighted_avg_gain:.2f}"

            # Check if reconfiguration is needed
            if float(weighted_avg_gain) < 0:
                message = f"\n⚠️ Weighted average gain is negative. Press Process Query button to reconfigure {param}."
                yield message
                print("Exiting Monitoring Agent\n\n")
                return {"next": "config_agent", "agent_id": "monitoring_agent", 
                       "messages": [('assistant', message)], "average_kpis_df": None, 
                       "vars_current": state["vars_current"], "vars_new": None, "weighted_average_gain": None}

        except Exception as e:
            error_message = f"Error: Monitoring Agent encountered an error on {param} due to {str(e)}\n"
            print(error_message)
            yield error_message
            return {"next": None, "agent_id": "monitoring_agent", "messages": [('assistant', error_message)], 
                   "average_kpis_df": None, "vars_current": state["vars_current"], "vars_new": None, "weighted_average_gain": None}

    # Reset monitoring display
    yield "reset"
    return {"next": None, "agent_id": "monitoring_agent", "messages": state["messages"], 
           "average_kpis_df": None, "vars_current": state["vars_current"], "vars_new": None, "weighted_average_gain": None}


def config_agent(state: State) -> State:
    """
    Restored Original Configuration Agent
    
    This agent:
    - Interprets user queries to detect target parameter
    - Analyzes historical data using SQL queries
    - Calculates weighted average gain for different values
    - Recommends optimal parameter changes
    """
    
    print("\n\nInside Config Agent") 
    
    # Initialize LLM agent with original tools
    llm = init_agent()
    system_prompt = 'You are an agent in a LangGraph. Your task is to help a user configure/analyse a current 5G network. You must reply to the questions asked concisely, and exactly in the format directed to you.'
    llm_agent = create_react_agent(llm, tools=[find_value_in_gnb, execute_historical_sql, calc_weighted_average], prompt=system_prompt)
    
    config = yaml.safe_load(open('config.yaml', 'r'))
    vars_new = {}
    
    # Extract user query from messages
    user_query = ""
    for message in state["messages"]:
        if isinstance(message, tuple) and message[0] == "human":
            user_query = message[1]
            break
        elif hasattr(message, 'content'):
            user_query = message.content
            break

    # Determine which parameter is being asked about
    param = None
    query_lower = user_query.lower()
    
    if "p0" in query_lower or "nominal" in query_lower:
        param = "p0_nominal"
    elif "dl" in query_lower and ("carrier" in query_lower or "bandwidth" in query_lower):
        param = "dl_carrierBandwidth"
    elif "ul" in query_lower and ("carrier" in query_lower or "bandwidth" in query_lower):
        param = "ul_carrierBandwidth"  
    elif "att_tx" in query_lower or ("att" in query_lower and "tx" in query_lower):
        param = "att_tx"
    elif "att_rx" in query_lower or ("att" in query_lower and "rx" in query_lower):
        param = "att_rx"

    if not param:
        error_message = """Error: 🚨 Failed to extract relevant parameter from query.
        Please make sure to restrict questions to permitted parameters only: p0_nominal, dl_carrierBandwidth, ul_carrierBandwidth, att_tx, att_rx
        
        Some examples of supported questions are:
        - What is the best value of p0 nominal?
        - Help me optimize dl carrierbandwidth.
        - My current ul carrierbandwidth value is 51. Is there a better value for my network?"""
        return {"next": None, "agent_id": "config_agent", "messages": state["messages"]+[("assistant", error_message)], 
               "average_kpis_df": None, "weighted_average_gain": None, "vars_current": state["vars_current"], "vars_new": None}

    print(f"Processing parameter: {param}")

    try:
        # Extract current parameter value from query or config
        current_value_prompt = f'''You are given a user query. Understand what is the current value of {param} selected by the user. 
        You should ONLY output the value of {param} exclusively, for example: '103', or '-10'. 
        USER_QUERY: {user_query}. 
        If you do not find the {param} value in this query, you can call the tool called `find_value_in_gnb` to find the value of the parameter.
        Make sure that your final output should just be the integer value of the respective parameter.
        
        Sample outputs:
        value: -106
        value: 90'''

        llm_response = llm_agent.invoke({"messages": current_value_prompt})
        current_value = int(llm_response["messages"][-1].content.split(":")[-1].strip().strip(".").strip("(){}"))
        
        if current_value not in config[f"{param}_values"]:
            raise ValueError(f"Extracted value {current_value} is not in allowed values {config[f'{param}_values']}")

    except Exception as e:
        error_message = f"""Error: 🚨 Failed to extract current {param} value from LLM response.
        LLM Raw Response: {llm_response["messages"][-1].content if 'llm_response' in locals() else 'No response'}
        Error: {str(e)}"""
        return {"next": None, "agent_id": "config_agent", "messages": state["messages"]+[("assistant", error_message)], 
               "average_kpis_df": None, "weighted_average_gain": None, "vars_current": state["vars_current"], "vars_new": None}

    try:
        # Query historical database for KPI analysis
        historical_sql_prompt = f'''Your task is to create a SQL query, execute it using the execute_historical_sql tool to get the proper result dataframe, and return the resulting answer dataframe.
        If you get error, make another call with proper SQL to the tool to get proper answer.
        There is a table called "kpis" with columns "Parameter", "Value", "snr", "bitrate_DL".
        The Value column shows the value of the corresponding Parameter.
        Write an SQL query which does the following:
        1. Filter rows where "Parameter" value matches the parameter for {param}.
        2. Find average of relevant KPIs FOR EACH of these distinct "Value" separately: {config[f'{param}_values']}
        The SQL query should return the columns in given order with proper averages.
        Order rows by DESCENDING order of parameter value.
        Also add filter to remove rows where KPI values are 0.
        You should only print the dataframe, with column names, received from the execute_historical_sql tool in following format: "data_frame : ,explanation: "'''

        llm_response = llm_agent.invoke({"messages": historical_sql_prompt})
        average_kpis_df = llm_response["messages"][-2].content if hasattr(llm_response["messages"][-1], "content") else None
        
        if not average_kpis_df:
            raise ValueError("Error: LLM agent did not return historical data.")

    except Exception as e:
        error_message = f"🚨 Error: Failed to query historical database. Details: {str(e)}"
        return {"next": None, "agent_id": "config_agent", "messages": state["messages"]+[("assistant", error_message)], 
               "average_kpis_df": None, "weighted_average_gain": None, "vars_current": state["vars_current"], "vars_new": None}

    try:
        # Calculate weighted average gain
        weight1, weight2 = config[f'{param}_WA_weights']
        calc_prompt = f'''Your task is to calculate the weighted average gain using the `calc_weighted_average` tool.
        Here are the inputs:
        1. `data_frame`: {average_kpis_df}
        2. `weight1`: {weight1}
        3. `weight2`: {weight2}
        4. `current_param_value`: {current_value}
        Use the tool to calculate the weighted average gain. Return **only** the resulting DataFrame as the output.'''

        llm_response = llm_agent.invoke({"messages": calc_prompt})
        weighted_avg = llm_response["messages"][-2].content if hasattr(llm_response["messages"][-1], "content") else None
        
        if not weighted_avg:
            raise ValueError("Error: Failed to calculate weighted average gain.")

    except Exception as e:
        error_message = f"🚨 Error: Failed to calculate weighted average gain. Details: {str(e)}"
        return {"next": None, "agent_id": "config_agent", "messages": state["messages"]+[("assistant", error_message)], 
               "average_kpis_df": average_kpis_df, "weighted_average_gain": None, "vars_current": state["vars_current"], "vars_new": None}

    try:
        # Generate final recommendation
        recommendation_prompt = f'''The table contains weighted average gain data for {param} values. Use only the data in the table to answer questions.
        
        Rules:
        1. The final recommendation is determined by the **greatest** 'Weighted Average Gain' value.
        2. Refer to the table explicitly for your answer. Think step by step.
        3. Negative Weighted Average Gain suggests the change is **not** recommended.
        4. If all changes result in negative gains, inform the user that no change is needed.

        Think step by step. Answer in this format: "Reason:, Answer: new_value"
        The "Answer" should be the new {param} value ONLY. If there is no change needed, write the current value only.
        **DO NOT use any tools**'''

        llm_response = llm_agent.invoke({"messages": recommendation_prompt})
        new_value = int(float(llm_response["messages"][-1].content.split('Answer: ')[1].split(',')[0]))
        vars_new[param] = new_value
        
        return {"next": "Validation Agent", "agent_id": "config_agent", 
               "messages": state["messages"]+[("assistant", llm_response["messages"][-1].content)], 
               "average_kpis_df": average_kpis_df, "weighted_average_gain": weighted_avg, 
               "vars_current": state["vars_current"], "vars_new": vars_new}

    except Exception as e:
        error_message = f"""Error: 🚨 Failed to extract new value of {param}.
        LLM Raw Response: {llm_response["messages"][-1].content if 'llm_response' in locals() else 'No response'}
        Error: {str(e)}"""
        return {"next": None, "agent_id": "config_agent", "messages": state["messages"]+[("assistant", error_message)], 
               "average_kpis_df": average_kpis_df, "weighted_average_gain": weighted_avg, "vars_current": state["vars_current"], "vars_new": None}


def valid_agent(state: State) -> State: 
    """
    Restored Original Validation Agent
    
    This agent:
    1. Applies new parameter to gNodeB configuration
    2. Restarts network and collects fresh KPIs
    3. Calculates weighted average gain to assess improvement
    4. Reverts to previous config if performance degrades
    5. Confirms success if performance improves
    """
    
    print("\n\nInside Validation Agent")

    # Initialize LLM agent  
    llm = init_agent()
    system_prompt = '''You are an agent in a LangGraph. Your task is to help a user validate and analyse a 5G network. You must reply to the questions asked concisely, and exactly in the format directed to you.'''
    llm_agent = create_react_agent(llm, tools=[execute_xapp_sql, calc_weighted_average], prompt=system_prompt)
    
    # Persist current config and stop network
    update_value_in_db(state["vars_current"])
    stop_network()

    # Identify which parameter changed
    param = None
    for key in state["vars_new"].keys():
        if state["vars_new"][key] != state["vars_current"][key]:
            param = key
            break

    if not param:
        error_message = "🚨 Error: No parameter change detected."
        yield {"next": None, "agent_id": "valid_agent", "messages": state["messages"] + [("assistant", error_message)], 
               "average_kpis_df": None, "weighted_average_gain": None, "vars_current": state["vars_current"], "vars_new": None}
        return

    # Fallback function to revert configuration
    def fallback_to_prev_config(param):
        if check_network_status():
            stop_network()
        update_value_in_gnb(param, state["vars_current"][param])
        start_network()

    try:
        # Apply new parameter and restart network
        update_value_in_gnb(param, state["vars_new"][param])
        
        # Handle special case for DL/UL carrier bandwidth sync
        if param == "dl_carrierBandwidth":
            state["vars_new"]["ul_carrierBandwidth"] = state["vars_new"]["dl_carrierBandwidth"]
        elif param == "ul_carrierBandwidth":
            state["vars_new"]["dl_carrierBandwidth"] = state["vars_new"]["ul_carrierBandwidth"]
            
        start_network()
        yield f"✅ Network initiated with {param} = {state['vars_new'][param]}"

        # Wait for validation period and collect new KPIs
        validation_wait_time = yaml.safe_load(open('config.yaml', 'r'))['validation_wait_time']
        yield f"✅ Collecting KPIs for new {param} for {validation_wait_time} second(s)..."
        time.sleep(validation_wait_time)
        update_value_in_db(state["vars_new"])

        # Generate SQL to collect validation data
        config = yaml.safe_load(open('config.yaml', 'r'))
        
        if param in ["p0_nominal", "dl_carrierBandwidth", "att_tx"]:
            sql_columns = f"tstamp", "pusch_snr", param, "dl_aggr_tbs"
            kpi_calculations = '''1. Makes another new column called "bitrate_dl", such that bitrate_dl[i] = max(0, (1000* (dl_aggr_tbs[i]-dl_aggr_tbs[i-1]))/(tstamp[i]-tstamp[i-1]))
            2. Makes a new column called "snr", such that snr[i] = pusch_snr[i]
            3. Finds the average of "bitrate_dl" and "snr"'''
            return_columns = f'"{param}","Average_of_bitrate_dl", "Average_of_snr"'
        else:  # ul_carrierBandwidth, att_rx
            sql_columns = f"tstamp", "dl_harq_round0", "dl_harq_round1", "dl_harq_round2", "dl_harq_round3", param, "ul_aggr_tbs"
            kpi_calculations = '''1. Makes another new column called "bitrate_ul", such that bitrate_ul[i] = max(0, (1000* (ul_aggr_tbs[i]-ul_aggr_tbs[i-1]))/(tstamp[i]-tstamp[i-1]))
            2. Makes a new column called "retx", such that retx[i] = (1000*(dl_harq_round0[i] + dl_harq_round1[i] + dl_harq_round2[i] + dl_harq_round3[i] - dl_harq_round0[i-1] - dl_harq_round1[i-1] - dl_harq_round2[i-1] - dl_harq_round3[i-1]) )/ (tstamp[i]-tstamp[i-1])
            3. Finds the average of "bitrate_ul" and "retx"'''
            return_columns = f'"{param}","Average_of_bitrate_ul", "Average_of_retx"'

        validation_sql_prompt = f'''Your task is to create a SQL query, execute it using the execute_xapp_sql tool EXACTLY ONCE, and return the resulting answer dataframe.
        Do not make multiple calls to the tool. 
        There is a table called "{config['table_name']}" with columns {sql_columns}.
        Write the SQL query which does the following:
        {kpi_calculations} for these values of "{param}": {state["vars_new"][param]}, {state["vars_current"][param]}
        The SQL query should return me these columns in this order: {return_columns}. 
        You should only print the dataframe, with column names, received from the execute_xapp_sql tool in following format: "data_frame : ,explanation: "'''

        llm_response = llm_agent.invoke({"messages": validation_sql_prompt})
        average_kpis_df = llm_response["messages"][-2].content if hasattr(llm_response["messages"][-1], "content") else None
        yield "✅ Aggregated data based on new KPI values"

    except Exception as e:
        error_message = f"🚨 Error: Failed to configure and collect new KPIs. Details: {str(e)}"
        yield error_message
        yield "⚠️ Reverting to previous stable configuration..."
        fallback_to_prev_config(param)
        yield {"next": None, "agent_id": "valid_agent", "messages": state["messages"] + [("assistant", error_message)], 
               "average_kpis_df": None, "weighted_average_gain": None, "vars_current": state["vars_current"], "vars_new": None}
        return 

    try:
        # Calculate weighted average gain for validation
        weight1, weight2 = yaml.safe_load(open('config.yaml', 'r'))[f'{param}_WA_weights']
        
        calc_prompt = f'''Your task is to calculate the weighted average gain using the `calc_weighted_average` tool.
        Here are the inputs:
        1. `data_frame`: {average_kpis_df}
        2. `weight1`: {weight1}
        3. `weight2`: {weight2}  
        4. `current_param_value`: {state["vars_current"][param]}
        5. `new_param_value`: {state["vars_new"][param]}
        Use the tool to calculate the weighted average gain. Return **only** the resulting numeric value.'''

        llm_response = llm_agent.invoke({"messages": calc_prompt})
        weighted_avg_val = float(llm_response["messages"][-1].content.strip())

    except Exception as e:
        error_message = f"🚨 Error: Failed to calculate weighted average gain. Details: {str(e)}"
        yield error_message
        yield {"next": None, "agent_id": "valid_agent", "messages": state["messages"] + [("assistant", error_message)], 
               "average_kpis_df": None, "weighted_average_gain": None, "vars_current": state["vars_current"], "vars_new": None}
        return 

    try:
        # Evaluate performance and make decision
        if float(weighted_avg_val) < 0:
            yield f'''⚠️ Recommendation: Revert to Previous {param} Value Due to Reduced Weighted Gain'''
            update_value_in_db(state["vars_new"])
            yield "⚠️ Reverting to previous stable configuration..."
            fallback_to_prev_config(param)
            yield f"⚠️ {param} value updated to {state['vars_current'][param]} in gNodeB configuration file"
        else:
            state["vars_current"][param] = state["vars_new"][param]
            
            # Sync DL/UL carrier bandwidth
            if param == "dl_carrierBandwidth":
                state["vars_current"]["ul_carrierBandwidth"] = state["vars_current"]["dl_carrierBandwidth"]
            elif param == "ul_carrierBandwidth":
                state["vars_current"]["dl_carrierBandwidth"] = state["vars_current"]["ul_carrierBandwidth"]
                
            yield "✅ New configuration is optimal and stable."
                
    except Exception as e:
        error_message = f"🚨 Error: Failed to validate weighted average gain value. Reason: {str(e)}"
        yield error_message
        yield {"next": None, "agent_id": "valid_agent", "messages": state["messages"] + [("assistant", error_message)], 
               "average_kpis_df": None, "weighted_average_gain": None, "vars_current": state["vars_current"], "vars_new": None}
        return  

    yield {"next": None, "agent_id": "valid_agent", "messages": state["messages"], 
           "average_kpis_df": average_kpis_df, "weighted_average_gain": weighted_avg_val, 
           "vars_current": state["vars_current"], "vars_new": None}
    return


def test_NIM():
    """Test NIM connectivity"""
    try:
        llm = init_agent()
        response = llm.invoke([HumanMessage(content="Hello")])
        return "NIM access verified successfully."
    except Exception as e:
        return f"Error encountered while testing access to local NIM or API Catalog: {str(e)}"


# Run standalone test if executed directly
if __name__ == "__main__":
    print("Testing restored agents...")
    try:
        result = test_NIM()
        print(f"NIM Test: {result}")
        print("✅ Restored agents file loaded successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")