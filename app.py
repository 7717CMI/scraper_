import streamlit as st
import json
import pandas as pd
from io import StringIO
import csv

st.set_page_config(
    page_title="Apollo Scraper - JSON to CSV Converter",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Apollo Scraper")
st.markdown("Paste JSON data from each Apollo page below. All data will be combined into a single CSV.")

# Helper function to extract people/contacts data from JSON (universal)
def extract_people_data(json_data):
    """Extract and flatten people/contacts data from JSON - handles both structures"""
    rows = []
    
    # Check for both 'people' and 'contacts' arrays
    data_list = json_data.get("people", []) or json_data.get("contacts", [])
    
    for person in data_list:
        # Extract basic person information
        row = {
            "id": person.get("id", ""),
            "name": person.get("name", ""),
            "first_name": person.get("first_name", ""),
            "last_name": person.get("last_name", ""),
            "title": person.get("title", ""),
            "headline": person.get("headline", ""),
            "linkedin_url": person.get("linkedin_url", ""),
            "city": person.get("city", ""),
            "state": person.get("state", ""),
            "country": person.get("country", ""),
            "postal_code": person.get("postal_code", ""),
            "formatted_address": person.get("formatted_address", ""),
            "time_zone": person.get("time_zone", ""),
            "seniority": person.get("seniority", ""),
            "organization_id": person.get("organization_id", ""),
            "organization_name": person.get("organization_name", ""),
        }
        
        # Extract email information (handles both direct email and contact_emails array)
        primary_email = person.get("email", "")
        email_status = person.get("email_status", "")
        email_true_status = person.get("email_true_status", "")
        
        # If contact_emails array exists, get primary email from there
        contact_emails = person.get("contact_emails", [])
        if contact_emails and not primary_email:
            primary_email = contact_emails[0].get("email", "")
            if not email_status:
                email_status = contact_emails[0].get("email_status", "")
            if not email_true_status:
                email_true_status = contact_emails[0].get("email_true_status", "")
        
        # Get all emails (for contacts with multiple emails)
        all_emails = [primary_email] if primary_email else []
        if contact_emails:
            all_emails.extend([e.get("email", "") for e in contact_emails if e.get("email") and e.get("email") != primary_email])
        all_emails = [e for e in all_emails if e]  # Remove empty strings
        
        row["email"] = primary_email
        row["email_status"] = email_status
        row["email_true_status"] = email_true_status
        row["all_emails"] = ", ".join(all_emails) if all_emails else ""
        
        # Extract phone numbers (handles both direct phone and phone_numbers array)
        phone_numbers = person.get("phone_numbers", [])
        if phone_numbers:
            primary_phone = phone_numbers[0].get("raw_number", "") or phone_numbers[0].get("sanitized_number", "")
            all_phones = [p.get("raw_number", "") or p.get("sanitized_number", "") for p in phone_numbers if p.get("raw_number") or p.get("sanitized_number")]
            all_phones = [p for p in all_phones if p]  # Remove empty strings
            row["phone"] = primary_phone
            row["all_phones"] = ", ".join(all_phones) if all_phones else ""
        else:
            # Fallback to direct phone fields
            row["phone"] = person.get("phone", "") or person.get("sanitized_phone", "")
            row["all_phones"] = row["phone"]
        
        # Extract organization details (handles both nested organization object and direct fields)
        org = person.get("organization", {})
        if org:
            # Nested organization object (people structure)
            row["org_name"] = org.get("name", "") or person.get("organization_name", "")
            row["org_website"] = org.get("website_url", "")
            row["org_linkedin"] = org.get("linkedin_url", "")
            row["org_employees"] = org.get("estimated_num_employees", "")
            row["org_industries"] = ", ".join(org.get("industries", [])) if isinstance(org.get("industries"), list) else ""
            row["org_keywords"] = ", ".join(org.get("keywords", [])) if isinstance(org.get("keywords"), list) else ""
            row["org_phone"] = org.get("phone", "") or org.get("sanitized_phone", "")
            row["org_founded_year"] = org.get("founded_year", "")
        else:
            # Direct organization fields (contacts structure)
            row["org_name"] = person.get("organization_name", "")
            row["org_website"] = ""
            row["org_linkedin"] = ""
            row["org_employees"] = ""
            row["org_industries"] = ""
            row["org_keywords"] = ""
            row["org_phone"] = ""
            row["org_founded_year"] = ""
        
        # Additional fields that might be useful
        row["twitter_url"] = person.get("twitter_url", "")
        row["facebook_url"] = person.get("facebook_url", "")
        row["person_id"] = person.get("person_id", "")
        row["account_id"] = person.get("account_id", "")
        row["created_at"] = person.get("created_at", "")
        row["updated_at"] = person.get("updated_at", "")
        
        rows.append(row)
    
    return rows

# Create tabs for better organization
num_pages = 25
tabs = st.tabs([f"Page {i+1}" for i in range(num_pages)])

# Store all JSON inputs
json_inputs = {}

# Create text areas in each tab
for i, tab in enumerate(tabs):
    with tab:
        page_num = i + 1
        json_input = st.text_area(
            f"Paste JSON data from Page {page_num}",
            height=400,
            placeholder=f'Paste your JSON data from page {page_num} here...',
            key=f"page_{page_num}"
        )
        json_inputs[page_num] = json_input
        
        # Show character count
        if json_input:
            char_count = len(json_input)
            st.caption(f"📝 {char_count} characters")

# Convert button
if st.button("🔄 Convert All Pages to CSV", type="primary", use_container_width=True):
    all_rows = []
    pages_processed = 0
    pages_with_errors = []
    total_people = 0
    
    # Process each page
    for page_num in range(1, num_pages + 1):
        json_input = json_inputs.get(page_num, "")
        
        if json_input.strip():
            try:
                # Parse JSON
                data = json.loads(json_input)
                
                # Extract people data
                rows = extract_people_data(data)
                
                if rows:
                    all_rows.extend(rows)
                    pages_processed += 1
                    total_people += len(rows)
                    st.success(f"✅ Page {page_num}: {len(rows)} records extracted")
                else:
                    st.warning(f"⚠️ Page {page_num}: No people/contacts data found")
                    
            except json.JSONDecodeError as e:
                error_msg = f"❌ Page {page_num}: Invalid JSON format - {str(e)}"
                st.error(error_msg)
                pages_with_errors.append(page_num)
            except Exception as e:
                error_msg = f"❌ Page {page_num}: Error - {str(e)}"
                st.error(error_msg)
                pages_with_errors.append(page_num)
    
    # Generate CSV if we have data
    if all_rows:
        # Create DataFrame - no deduplication, keep all records as-is
        df = pd.DataFrame(all_rows)
        
        # Display summary
        st.divider()
        st.success(f"🎉 Successfully processed {pages_processed} page(s) with {total_people} total records!")
        st.info(f"📊 Total records in CSV: {len(df)} (all records included, no duplicates removed)")
        
        if pages_with_errors:
            st.warning(f"⚠️ {len(pages_with_errors)} page(s) had errors: {', '.join(map(str, pages_with_errors))}")
        
        # Display preview
        st.subheader("📋 Data Preview")
        st.dataframe(df, use_container_width=True, height=400)
        
        # Convert to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        csv_data = csv_buffer.getvalue()
        
        # Download button
        st.download_button(
            label=f"📥 Download CSV ({len(df)} records)",
            data=csv_data,
            file_name="linkedin_contacts_combined.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Show statistics
        st.subheader("📊 Statistics")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Records", len(df))
        with col2:
            st.metric("Pages Processed", pages_processed)
        with col3:
            st.metric("With Email", len(df[df["email"] != ""]))
        with col4:
            if "email_status" in df.columns:
                verified_count = len(df[df["email_status"].astype(str).str.lower() == "verified"])
            else:
                verified_count = 0
            st.metric("Verified Emails", verified_count)
        with col5:
            st.metric("Unique Countries", df["country"].nunique())
        
        # Additional stats
        col6, col7, col8 = st.columns(3)
        with col6:
            st.metric("Unique Companies", df["org_name"].nunique() if "org_name" in df.columns else 0)
        with col7:
            c_suite_count = len(df[df["seniority"] == "c_suite"])
            st.metric("C-Suite", c_suite_count)
        with col8:
            vp_count = len(df[df["seniority"] == "vp"])
            st.metric("Vice Presidents", vp_count)
            
    else:
        st.error("❌ No data found in any of the pages. Please paste JSON data in at least one page.")

# Instructions
with st.expander("ℹ️ Instructions"):
    st.markdown("""
    ### How to use:
    1. Navigate through the page tabs (Page 1, Page 2, etc.)
    2. Copy the raw JSON data from each Apollo page
    3. Paste it into the corresponding page tab
    4. Repeat for all pages you want to include
    5. Click "Convert All Pages to CSV" button
    6. Review the preview and statistics
    7. Click "Download CSV" to save the combined file
    
    ### Features:
    - ✅ Combines data from multiple pages
    - ✅ Shows processing status for each page
    - ✅ Displays comprehensive statistics
    - ✅ Handles errors gracefully (skips invalid pages)
    - ✅ All records included (no duplicates removed)
    
    ### Supported JSON formats:
    The app automatically detects and handles both formats:
    
    **Format 1 - People structure:**
    - JSON with a `people` array
    - Nested `organization` object with company details
    - Direct email and phone fields
    
    **Format 2 - Contacts structure:**
    - JSON with a `contacts` array
    - `contact_emails` array for multiple emails
    - `phone_numbers` array for multiple phones
    - Direct `organization_name` field
    
    Both formats are automatically detected and converted to a unified CSV structure.
    
    ### Tips:
    - You don't need to fill all 25 pages - only paste data in the pages you have
    - Empty pages will be skipped automatically
    - All records are included in the CSV (no duplicates removed)
    """)
