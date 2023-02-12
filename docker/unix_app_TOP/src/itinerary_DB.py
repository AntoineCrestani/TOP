from pymongo import MongoClient
import json, csv, os
import pandas as pd
import haversine as hs
from itinerary_ML import Itinerary_ML as IT_ML
import subprocess
ADJUSTED_TYPES = [
    "AffordableAccomodation",
    "Artistic",
    "Convenience",
    "Drinks",
    "HotelAccomodation",
    "Leisure",
    "NaturalHeritage",
    "LocalCulture",
    "Neutral",
    "SitDown",
    "SportsPlace",
    "TakeAway",
    "CulturalBuilding",
    "Tour"
]



'''api = FastAPI(
    title="Itinerary Vacance",
    description="To get an itinerary for a vacation in Occitanie, based on different profiles.",
    version="0.0.7"
)'''


#@api.get('/')
'''def get_index():
    return {
        'Greetings': 'Welcome to the awesome site where you can get your vacation itinerary, for each day, based on your interests. Check it out'
    }'''


#@api.get('/pois')

class Itinerary_DB():
    def __init__(self, user_profile):
        dummy_city = user_profile["u_city"]
        sa = self.get_db_obj()
        coll_poi = sa.poi
        coll_cat = sa.category

        #creating poi profiles
        self.dict_cat = self.db_category_to_metatype(coll_cat.find({}))
        self.all_pois = self.db_all_pois_category_to_pois_metatypes(coll_poi.find({},{"_id": 1, "lat": 1, "long": 1, "alt_id": 1, "name": 1, "id_categories": 1}))

        #getting random poi within the city
        
        random_POIs_in_city_cursor = coll_poi.aggregate([{"$match": {"address.city": dummy_city}}, { "$sample": { "size": 3 } }, {"$project": {"_id": 1,"name":1, "lat": 1, "long": 1}}])
        random_POIs_in_city = []
        print("names are : ")
        for poi in random_POIs_in_city_cursor:
            print(str(poi.get("name")))
            random_POIs_in_city.append({"lat": float(poi.get("lat")), "long": float(poi.get("long")), "name": poi.get("name"), "id": str(poi.get("_id"))})
        
        # just to be safe, when city given has no POI
        self.nearest_POI_ID = ""
        if len(random_POIs_in_city) > 0:
            self.nearest_POI_ID = self.get_nearest_point(random_POIs_in_city[0]["lat"], random_POIs_in_city[0]["long"])
        user_profile["u_id"] = self.nearest_POI_ID

        df_POIs = pd.DataFrame(self.all_pois)

        if self.nearest_POI_ID =="":
            #if all else, take random POI as nearest. 
            user_profile["u_id"]="63e4fbc1a5b6bc28e111fe78"
            print("we use the dummy one for some reason")
        self.it_ml = IT_ML(df_POIs, user_profile, 123)
        self.final_itinerary = self.get_final_itinerary(user_profile, df_POIs)
    def get_db_obj(self):
        client = MongoClient(
            host="127.0.0.1",
            port = 27017
        )
        sa = client.test_eval

        if len(sa.list_collection_names()) == 0:
            subprocess.run(["mongorestore", "-d", "test_eval", os.path.join(os.getcwd(), "dump/test_eval/")])
        return sa

    def db_category_to_metatype(self, cursor_cats):
        #creates the POI profiles
        #load typesAdapter.csv for types to supertypes relation
        df_super_type_adapter = pd.read_csv(os.path.join(os.getcwd(), "dump/TypesAdapter.csv"))
        dict_cat = {}
        for cat in cursor_cats:
            df_c_type = df_super_type_adapter[df_super_type_adapter["Types"]==(cat.get("name").replace("schema:",""))]["AdjustedTypes"]
            if len(df_c_type) > 0:

                dict_cat[str(cat.get("_id"))] = df_c_type.iloc[0]
        return dict_cat

    def category_to_metatype(self, id_categories):
        id_to_meta_list = []
        for id in id_categories:
            if str(id) in self.dict_cat:
                if self.dict_cat[str(id)] not in id_to_meta_list:
                    id_to_meta_list.append(self.dict_cat[str(id)])

        return id_to_meta_list

    def db_all_pois_category_to_pois_metatypes(self, cursor_pois):
        pois = []
        for poi in cursor_pois:
            row = {"lat": float(poi.get("lat")), "long": float(poi.get("long")), "name": poi.get("name"), "id": str(poi.get("_id"))}
            if abs(float(row["lat"])) < 90.0 and abs(float(row["lat"])) > 0.0 and abs(float(row["long"])) < 180.0 and abs(float(row["long"])) > 0.0:
                id_categories = poi.get("id_categories")
                id_to_meta_list = self.category_to_metatype(id_categories)
                
                for m_t in ADJUSTED_TYPES:
                    row[m_t] = 1 if m_t in id_to_meta_list else 0

                pois.append(row)

        return pois

    def get_nearest_point(self, lat, lon):
        app_df=pd.DataFrame.from_dict(self.all_pois)
        #Ensemble des coordonnées
        app_df["Coord"] = list(zip(app_df["lat"], app_df["long"])) # Coord tupples

        # Calcul de la distance au point de départ
        app_df["Distance_start_point"] = app_df["Coord"].apply(lambda point: hs.haversine((lat, lon), point))
        
        min_dist_idx=app_df["Distance_start_point"].idxmin()

        return app_df.iloc[min_dist_idx]["id"]

    def get_final_itinerary(self, user_profile, df_POIs):        
        final_itinerary_poi_ids_per_day = self.it_ml.global_itineraire
        final_itinerary_POIs = {}
        df_POIs["id"] = df_POIs["id"].apply(str)
        for day in final_itinerary_poi_ids_per_day.keys():
            pois_ids = final_itinerary_poi_ids_per_day[day]
            
            pois_df = df_POIs[df_POIs["id"].isin(pois_ids)]
            pois_df = pois_df[["lat", "long", "name", "id"]]
            final_itinerary_POIs[day] = pois_df.to_json(orient='records')

        return final_itinerary_POIs