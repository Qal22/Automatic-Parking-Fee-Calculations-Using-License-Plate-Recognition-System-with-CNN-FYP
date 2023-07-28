import streamlit as st
import database as db
from datetime import datetime
import base64
import requests
import re

st.set_page_config(page_title="Parking Fee Calculations", page_icon="🧮")

url = "https://www.billplz-sandbox.com/api/v3/bills"
auth_token = "9288fb34-398d-4c69-ad44-9ba08b97f51f"
collection_id = "j0vsf4ht"
# Base64-encode the token
encoded_auth_token = base64.b64encode(f"{auth_token}:".encode()).decode()

if 'billplz[id]' in st.experimental_get_query_params():
    valuefromlink = st.experimental_get_query_params().get('billplz[id]', [''])[0]
    urlWithparam = st.experimental_get_query_params()
    receipturl = 'https://www.billplz-sandbox.com/bills/' + valuefromlink
    getBillurl = 'https://www.billplz-sandbox.com/api/v3/bills/' + valuefromlink

    headers = {
        "Authorization": f"Basic {encoded_auth_token}:",
    }

    response = requests.get(getBillurl, headers=headers)

    if response.status_code == 200:
        bill_data = response.json()
        if bill_data['paid'] == True:
            st.success("The parking fee payment paid successfully")
            st.markdown(f"[Receipt]( {receipturl} )", unsafe_allow_html=True)
            db.del_lpn(bill_data['description'])
        else:
            st.error("The payment failed, please try again")
    else:
        st.error(f"Failed to fetch bill. Status Code: {response.status_code}")

    st.experimental_set_query_params()

currentTime = datetime.now().strftime('%H:%M:%S')
hourly_rate = 5

enter_button = False
fee = 0

st.title("Parking Fee Calculations")

st.sidebar.success("Select a page above")

def clear_text():
    st.session_state["textInput"] = ""
    st.session_state["full_name"] = ""
    st.session_state["email"] = ""

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

with st.form(key="myform", clear_on_submit=True):
    st.header("Parking Rate: RM" + str(hourly_rate) + " per hour")

    licensePlate_number = st.text_input("Enter your license plate number", key = "textInput")

    fullName = st.text_input("Your Full Name", key="full_name")

    email = st.text_input("Your e-mail", key="email")

    col1, col2, col3 = st.columns([1,1,6])
    with col1:
        enter_button = st.form_submit_button("Enter")
    with col2:
        clear_button = st.form_submit_button("Clear", on_click=clear_text)

if clear_button:
    enter_button = False

if enter_button:
    if not licensePlate_number:
        st.warning("Please enter your license plate number")
    elif not fullName:
        st.warning("Please enter your full name")
    elif not email:
        st.warning("Please enter your email")
    elif not is_valid_email(email):
            st.warning("Please enter a valid email address.")
    else:
        with st.container():
            st.write("---")
            licensePlate_number = licensePlate_number.replace(" ", "").upper()
            time = db.get_lpn(licensePlate_number)

            if time is not None:
                st.text_input("License Plate Number", value=licensePlate_number, disabled=True)
                st.text_input("Name", value=fullName, disabled=True)
                st.text_input("Email", value=email, disabled=True)
                st.text_input("Time in", value=time["time"], disabled=True)
                st.text_input("Time out", value=currentTime, disabled=True)
                
                start_time = datetime.strptime(time["time"], "%H:%M:%S")
                end_time = datetime.strptime(currentTime, "%H:%M:%S")
                time_difference = end_time - start_time
                duration_seconds = int(time_difference.total_seconds())
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                seconds = duration_seconds % 60
                duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                st.text_input("Duration", value=duration, disabled=True)
                
                hours, minutes, seconds = map(int, duration.split(':'))
                total_minutes = hours * 60 + minutes
                fee = total_minutes // 60 * hourly_rate
                
                if total_minutes % 60 > 0:
                    fee += hourly_rate
                
                st.text_input("Parking Fee", value="RM {:.2f}".format(fee), disabled=True)
                
                data = {
                    "collection_id": collection_id,
                    "description": licensePlate_number,
                    "email": email,
                    "name": fullName,
                    "amount": fee*100,
                    "callback_url": "http://10.62.20.99:8501/Parking_Fee_Calculations",
                    "redirect_url": "http://10.62.20.99:8501/Parking_Fee_Calculations"
                }
                
                headers = {
                    "Authorization": f"Basic {encoded_auth_token}:",
                }
                
                response = requests.post(url, json=data, headers=headers)
                
                resultsresponse = response.json()
                #st.session_state = response.json()
                 
                st.write(f'<a href="{resultsresponse["url"]}" target="_self"><button>Pay</button></a>', unsafe_allow_html=True)
            else:
                st.warning("The license plate number entered is not found")
    
    enter_button = False