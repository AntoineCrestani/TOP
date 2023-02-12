
This project has the goal of creating vacation itinerares in Occitania, allowing for different user types and starting positions.
Uses dash and mongodb 
# File architecture
=> TOP
    _ dump => contains the data necessary to re create the database without re running the scraping script
    _ htmls => contains the maps created beforehand
    _ scraping  => contains the files for downloading the flux, unzipping it, scraping the contents , and creating the database 
    _ src => contains the dash app and other assets necessary ( city names, ML and DB scripts, user profiles...)
    _ useful => potentially useful commands ( deprecated)
    _ docker ( work in progress)
    _ deprecated => older code, probably not useful anymore ? 

/src
  has all the files necessary for execution of the code


# loading the data
go to scraping folder
run command :
  python json_data_to_mong.py

takes a couple minutes to run because it downloads a 250 mb file, unzips it into a 2gig folder, then impots that into a datatabase with added transformation 

to create the dump that is later used , go back to base directory  ( itin_vac_DST_eval )and run :
  mongodump -d test_eval -o ./dump


# once everything has been installed, having itin_vac_DST_eval as the working directory run the following command to have a Dash server running
python3 /src/itinerary_Dash.py

