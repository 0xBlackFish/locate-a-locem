import numpy as np
import altair as alt
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import streamlit as st
from getpass import getpass

st.set_page_config('LoL Demo',layout='wide',initial_sidebar_state='auto')
password = st.text_input('Enter the password to access the site: ')

if password == st.secrets['site_password']:

    ### Streamlit Design Elements ###
    radios = st.sidebar.radio('Pages',['Analysis','Proposal'])
    alt.data_transformers.disable_max_rows()

    if radios == 'Analysis':

        shifts_df = pd.read_csv('sample-data-shifts.csv',parse_dates=['Posted Date','Start Time','End Time'])
        users_df = pd.read_csv('sample-data-users.csv',parse_dates=['Created Date'])
        applications_df = pd.read_csv('sample-data-applications.csv')

        shifts_df['Latitude'] = shifts_df['Latitude'].apply(lambda x: float(x))


        # Create logic to restrict locations to only users and shifts located in the UK and Ireland
        s_long_params = (shifts_df['Longitude'] >= -12) & (shifts_df['Longitude'] <= 2)
        s_lat_params = (shifts_df['Latitude'] >= 50) & (shifts_df['Latitude'] <= 60)

        u_long_params = (users_df['Longitude'] >= -12) & (users_df['Longitude'] <= 2)
        u_lat_params = (users_df['Latitude'] >= 50) & (users_df['Latitude'] <= 60)

        shifts_mod_df = shifts_df[s_lat_params & s_long_params]
        users_mod_df = users_df[u_lat_params & u_long_params]


        # Aggregate user and shift data to get counts by location
        user_location_grp = users_mod_df.groupby(['Latitude','Longitude']).count()['User ID'].sort_values(ascending=False).reset_index()
        user_location_grp.rename({'User ID':'user_count'},inplace=True,axis=1)

        shifts_location_grp = shifts_mod_df.groupby(['Latitude','Longitude']).count()['Shift ID'].sort_values(ascending=False).reset_index()
        shifts_location_grp.rename({'Shift ID':'shift_count'},inplace=True,axis=1)


        st.title('Locate-a-Locem Sample Streamlit Demo')
        st.write('')
        st.write('')
        st.header('Where are users and shifts located?')
        st.write('')
        st.write('')
        st.write('')

        col_map, col_blank1, col_analysis_1 = st.beta_columns([3,1,3])


        # Mapping concentration of shifts vs. users
        with col_map:
            uk_counties = alt.topo_feature('https://raw.githubusercontent.com/deldersveld/topojson/master/countries/united-kingdom/uk-counties.json','GBR_adm2')
            ireland_counties = alt.topo_feature('https://raw.githubusercontent.com/deldersveld/topojson/master/countries/ireland/ireland-counties.json','IRL_adm1')

            uk_map = alt.Chart(uk_counties).mark_geoshape(stroke='white').encode(color=alt.value('grey')).properties(height=500,width=500)
            ireland_map = alt.Chart(ireland_counties).mark_geoshape(stroke='white').encode(color=alt.value('grey')).properties(height=500,width=500)
            map_geo = ireland_map + uk_map

            user_points = alt.Chart(user_location_grp).mark_circle(stroke='black',strokeWidth=0.1).encode(
                longitude='Longitude:Q',
                latitude='Latitude:Q',
                size=alt.Size('user_count',legend=None),
                color=alt.value('orange'),
                tooltip=[alt.Tooltip('user_count',title='User Count')]
            )

            shift_points = alt.Chart(shifts_location_grp).mark_circle().encode(
                longitude='Longitude:Q',
                latitude='Latitude:Q',
                size=alt.Size('shift_count',legend=None),
                color=alt.value('blue'),
                tooltip=[alt.Tooltip('shift_count',title='Shift Count')]
            )

            st.altair_chart((map_geo + shift_points + user_points).configure_view(strokeWidth=0),use_container_width=True)

        with col_analysis_1:
            st.write('## Understanding the View')
            st.write('Exhibit 1 is a map of the UK and Ireland, which has been plotted with user and shift locations. Users are represented by the color orange and shifts are represented by the color blue. The bigger the circle, the larger the concentration of users or shifts in that location. The maximum number of users in a single location is 465, and the maximum number of shifts in a single location was 240. Hover over the circles to see the shift count or user count.')
            st.write('')
            st.write('## Insights')
            st.write('Immediately, we see that users and shifts have contrasting patterns of dispersion. Users are concentratd in major urban centers like London, Greater Manchester, Liverpool, and Birmingham. Whereas shifts are spread throughout the country. In urban areas, demand for shifts is likely to meet, or even exceed supply. However, there appears to be a large number of shifts in areas with less user coverage, which could be leading to fewer applications.')

        st.write('')
        st.write('')

        # Exploring how many shifts users are eligible for based on travel radius
        st.header('How many shifts are available to users within their travel radius?')
        st.write('')
        st.write('')
        st.write('')

        df = pd.read_csv('shifts_in_radius.csv',parse_dates=['Created Date'])

        # Create bins for # of shifts in radius
        def travel_radius_bin(shifts_in_radius):
            label = '50+'
            
            if shifts_in_radius == 0:
                label = 'Zero'
            elif shifts_in_radius > 0 and shifts_in_radius <= 20:
                label = '1 - 20'
            elif shifts_in_radius > 20 and shifts_in_radius <= 50:
                label = '21 - 50'
            
            return label

        df['Travel Radius Band'] = df['shifts_in_radius'].apply(travel_radius_bin)

        col_hist, col_blank2, col_analysis_2 = st.beta_columns([3,1,3])

        with col_hist:
        
            histogram = alt.Chart(df[df['Created Date'] <= datetime(2021,3,1,0,0,0)]).mark_bar().encode(
                x=alt.X('shifts_in_radius',bin=alt.Bin(step=25),axis=alt.Axis(title='Shifts in Travel Radius', labelFontSize=12, labelPadding=10, titleFontSize=16, titlePadding=20)),
                y=alt.Y('count()',axis=alt.Axis(title='Count of Users',labelFontSize=12, labelPadding=10, titleFontSize=16, titlePadding=20)),
                tooltip=[alt.Tooltip('count()',title='Count of Users',format='#,')]
            ).properties(height=400,width=700)

            histogram_sub200 = alt.Chart(df[(df['Created Date'] <= datetime(2021,3,1,0,0,0)) & (df['shifts_in_radius'] <= 200)]).mark_bar().encode(
                x=alt.X('shifts_in_radius',bin=alt.Bin(step=5),axis=alt.Axis(title='Shifts in Travel Radius', labelFontSize=12, labelPadding=10, titleFontSize=16, titlePadding=20)),
                y=alt.Y('count()',axis=alt.Axis(title='Count of Users',labelFontSize=12, labelPadding=10, titleFontSize=16, titlePadding=20)),
                tooltip=[alt.Tooltip('count()',title='Count of Users',format='#,')]
            ).properties(height=400,width=700)

            st.subheader('All Users')
            st.write('')
            st.write('')
            st.altair_chart(histogram,use_container_width=True)
            st.subheader('Users with Less than 200 Shifts in Travel Radius')
            st.write('')
            st.write('')
            st.altair_chart(histogram_sub200,use_container_width=True)


        with col_analysis_2:
            st.write('')
            st.write('')
            st.write('## Understanding the View')
            st.write('Exhibit 2 is a histogram showing the count of users falling within each bin. Bins represent the number of shifts that were within a given user\'s stated travel radius. The sample user data contained 21,238 user records. Of these 754 users were created after March 1, 2021. In order to avoid biasing the analysis, these users were excluded from this section. This was to ensure that only users who were created prior to the start of the shift sample data were included.')
            st.write('')
            st.write('Exhibit 3 is the exact same histogram as Exhibit 2, but the x-axis has been truncated at 200 in order to show a more fine-grained view of the data. In both charts, you may hover over the bars to see the count of users within each bin.')
            st.write('')
            st.write('')
            st.write('')
            st.write('')
            st.write('## Insights')
            st.write('The data in both exhibits 2 and 3 is heavily skewed leftward, with the majority of users having 50 shifts or less within their designated travel radius. Of the 20,484 included in the sample, 74% (15,251) of users had 25 shifts or less in their designated travel radius. Within this specific group, 65% of users had 5 or fewer shifts. This means that a majority of users do not have shifts that are close enough to them to apply to, creating a shortage of supply.')

        st.write('')
        st.write('')

        # Placeholder Comment
        st.header('What is the relationship between a user\'s stated travel radius and the number of shifts they qualify for?')
        st.write('')
        st.write('')
        st.write('')

        col_scatter, col_blank3, col_analysis_3 = st.beta_columns([3,1,3])

        with col_scatter:

            scatter = alt.Chart(df[(df['Created Date'] <= datetime(2021,3,1,0,0,0)) & (df['Travel Radius'] <= 300)]).mark_circle(size=60).encode(
                x=alt.X('shifts_in_radius',axis=alt.Axis(title='Shifts in Travel Radius', labelFontSize=12, labelPadding=10, titleFontSize=16, titlePadding=20)),
                y=alt.Y('Travel Radius',axis=alt.Axis(title="User's Travel Radius",labelFontSize=12, labelPadding=10, titleFontSize=16, titlePadding=20)),
                color='Travel Radius Band'
            ).interactive().properties(height=400,width=700)

            st.altair_chart(scatter,use_container_width=True)

        with col_analysis_3:
            st.write('## Understanding the View')
            st.write('Exhibit 4 is a scatterplot comparing the user\'s stated travel radius with the number of shifts within their travel radius. Like exhibits 2 and 3, this view only includes users who were acquired on, or before, March 1, 2021. The y-axis has been truncated to 200 to exclude outliers, and to provide a more detailed look at how users are concentratd. The colors represent the range which a user falls into for the number of shifts that fall within their designated travel radius. This chart is interactive, and will allow you to zoom in and out.')
            st.write('')
            st.write('## Insights')
            st.write('The key callout here is that in many cases, even for users who list high travel radii, such as 100 km, we still observe a large amount of users with few shifts nearby. The non-linear shape of this plot supports the case for geographic concentration and supply shortages for many users/locations. Intuitively, you would expect that the larger a user\'s travel radius, the more shifts they would have available to them. However, this chart indicates that these variables are weakly correlated at best.')

        st.write('')
        st.write('')
        st.write('')
        st.header('Conclusion')
        st.write('''In conclusion, I believe there is a meaningful opportunity to dive deeper into this geographic phenomena to better understand the specific geographies and users who are being impacted. Potential adjustments to business strategy might include:
        
        * targeted campaigns to users telling them how many more shifts would be available to them with a modified travel radius
        * marketing campaigns to partner with pharmacies in these areas to offer more shifts
        
        ''')



    else:
        st.title('Proposal for Potential Areas of Exploration')
        st.write('')
        st.write('')
        st.header('1. Standup dedicated data resources')
        st.write('To aid in the delivery of high quality data analysis and data science projects, it makes sense to automate the data pipelines and host LoL\'s data in an environment that is meant for analytical purposes. The benefit of this is that it will keep additional strain off of your operational systems, and allow for analyses to be conducted in an environment meant to handle those kinds of loads. In addition, in a platform like Google Cloud or AWS, the native analytical tooling allows for deeper and more robust analyses and modeling. It would also lay a strong foundation for Locate-a-Locem as your data & analytics capacity grows over time. ')
        st.write('')
        st.write('')
        st.header('2. Deep Dives into Supply and Demand')
        st.write('As I stated in my analysis, I belive there are opportunities on both sides of the marketplace to improve the matching of supply and demand, which will ultimately lift application and booking rates. There are a variety of ways to explore this further, beginning with identifying the areas where a solid equalibrium exists and exploring why. These learnings will inform targeted strategies which the LoL team can implement to address the imbalance in other areas.')
        st.write('')
        st.write('')
        st.header('3. Cohort Analyses')
        st.write('This analytical approach could be applied to a variety of measures, but the two I would look at first are churn and core actions. By looking at these two, we can answer questions like, "is retention, as defined by users taking a core action for the product, improving for newer cohorts?" or "are users in certain markets better retained than those in others?"')
        st.write('')
        st.write('')
        st.write('I see a ton of potential in what Locate-a-Locem is offering and believe that now is the perfect time to move towards a more data-driven approach and invest in this capacity. I appreciate your consideration!')

else:
    st.write('Refresh the page and try entering the password again')
