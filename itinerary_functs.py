import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt

import seaborn as sns

import contextily as cx
import rasterio 
from rasterio.plot import show as rioshow
import haversine as hs
from sklearn.cluster import BisectingKMeans # Importing KMeans
import folium
import networkx as nx
import random
from operator import itemgetter
from sklearn.cluster import KMeans
from matplotlib.pyplot import cm
import time
from os.path import exists


USELESS_COLS = [
        # Informations de création de la donnée
        "Createur_de_la_donnee",
        "Date_de_mise_a_jour",
        "Periodes_regroupees",
        #adresse
        "Adresse_postale",
        "Code_postal_et_commune",
        "Contacts_du_POI",
        # Info covid 19
        "Covid19_mesures_specifiques",
        "Covid19_est_en_activite",
        "Covid19_periodes_d_ouvertures_confirmees",
        # Autre info inutile
        "SIT_diffuseur",
        "Classements_du_POI",
        "Description",   
    ]
    

ADJUSTED_TYPES=["AffordableAccomodation",
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
    "Tour"]
N_ADJ_TYPES=len(ADJUSTED_TYPES)


def setup_dataframe():
    datatourisme_df = pd.read_csv("datatourisme-reg-occ-20230123.csv")
    datatourisme_df = datatourisme_df.drop(USELESS_COLS, axis=1).drop_duplicates()
    datatourisme_df["URI_ID_du_POI"]=datatourisme_df["URI_ID_du_POI"].apply(lambda x: x.replace("https://data.datatourisme.fr/",""))
    type_adapter=pd.read_csv("TypesAdapter.csv",sep=",",header=0)
    type_adapter=type_adapter.drop_duplicates()
    return datatourisme_df,type_adapter



def clean_type(Categorie):
    #splitting and removing prefixes : 
    #           https://www.datatourisme.fr/ontology/core#
    #           http://schema.org/
    #           http://purl.org/ontology/olo/core#OrderedList
    out = [sub.replace('http://schema.org/', '').replace("https://www.datatourisme.fr/ontology/core#","").replace("http://purl.org/ontology/olo/core#","") for sub in Categorie.split("|")]
    return out
def get_adj_type(type_,type_adapter):
    return type_adapter.loc[type_adapter["Types"]==type_]["AdjustedTypes"].item()

def create_categories_deprecie(df,type_adapter):
    for index,row in df.iterrows():
        for type_ in clean_type(row["Categories_de_POI"]):
            adj_type=get_adj_type(type_,type_adapter)
            val=df.loc[index,adj_type]+1
            df.at[index,adj_type]=val
    df=df.drop(labels=["Categories_de_POI"],axis=1)
    return df

def create_categories_row(categories,type_adapter):
    dict_type=dict.fromkeys(ADJUSTED_TYPES, 0)
    for type_ in clean_type(categories):
        adj_type=get_adj_type(type_,type_adapter)
        dict_type[adj_type]+=1
    return dict_type

def create_categories(df,type_adapter):
    applied_df = df.apply(lambda row: create_categories_row(row["Categories_de_POI"],type_adapter), axis='columns', result_type='expand')
    datatourisme_df = pd.concat([df, applied_df], axis='columns')
    return datatourisme_df

def read_from_files():
    type_adapter=pd.read_csv("TypesAdapter.csv",sep=",",header=0)
    type_adapter=type_adapter.drop_duplicates()
    datatourisme_df=pd.read_csv("POI_categories.csv")
    return datatourisme_df,type_adapter


def calcule_score(df,profil):
    df["Score"]=df[ADJUSTED_TYPES].dot(profil)
    return df

def clean_latitude(df):
    LATITUDE_MINIMUM = 42.277342
    LATITUDE_MAXIMUM = 45.147210
    LONGITUDE_MINIMUM =-0.423264
    LONGITUDE_MAXIMUM = 5.000000
    df = df[df["Latitude"] < LATITUDE_MAXIMUM]
    df = df[df["Latitude"] > LATITUDE_MINIMUM]
    df = df[df["Longitude"] < LONGITUDE_MAXIMUM]
    df = df[df["Longitude"] > LONGITUDE_MINIMUM]
    return df


def is_hotel(POI):
    return max(POI["HotelAccomodation"].item(),POI["AffordableAccomodation"].item())==POI[ADJUSTED_TYPES].max(axis=1)
def is_restaurant(POI):
    return max(POI["TakeAway"].item(),POI["SitDown"].item())==POI[ADJUSTED_TYPES].max(axis=1)


#getting the indexes of hotels and restaurants.
def get_index_hotel_restaurant(df):

    i=0
    index_hotels=[]
    index_restaurants=[]
    for index in range(len(df)):
        if is_hotel(df.iloc[[index]]).item():
            index_hotels.append(index)
        if is_restaurant(df.iloc[[index]]).item():
            index_restaurants.append(index)
    return index_hotels,index_restaurants

def separate_hotel_restaurants(df):
    t1=time.time()
    index_hotels,index_restaurants=get_index_hotel_restaurant(df)
    t2=time.time()
    print("getting the indexes of hotels and restaurants took",t2-t1,"seconds")
    #on crée les df de restaurants et hotels
    hotels=df.iloc[index_hotels]      
    restaurants=df.iloc[index_restaurants]
    
    # on combine les deux listes d'indices pour éviter des problemes d'indexation
    to_remove = index_hotels + list(set(index_restaurants)-set(index_hotels))
    # on enleve les restaurants et hotels du df principal
    df=df.drop(df.index[to_remove])
    return hotels,restaurants,df






# fonctions de génération d'itinéraire.


#functions here
# score functions : 
#   get_score clusters : returns the mean score of all clusters
#   get_score_path : returns the score of a path
#   get_score_ajuste : returns the adjusted score for a POI . TO REMAKE

# Path finding functions :
#   findPaths : returns all the permutations of paths of specifed length from a node
#   get_best path : returns the path with the best score

# Itinerary finding functions :
#   get_itineraire :  returns the itinerary through one cluster in a list  [poi1,poi2,poi3]
#   get_next_POI :  from a current poi and a list of all non visited POIs within a cluster, returns the best POI to visit next.
#   get_global_itineraire :  returns a proper day to day itinerary in dict{"day_0": [POI1,POI2...]...})



def get_score_clusters(n_clusters,clustered):
    #returns the mean score of all clusters
    scores=[]
    for c in range(n_clusters):
        cluster=clustered[clustered["Cluster"]==c]
        scores.append((c,cluster["Score"].mean()))
    return scores

def get_score_path(path,score_clusters):
    #returns the score of a path
    return sum([score_clusters[node][1] for node in path])

def get_score_ajuste(score,distance):
    # returns the adjusted score for a POI . TO REMAKE
    # TODO IMPROVE this GREATLY. We had ideas with amey. A step function would be nice
    if distance<0.01:
        score_f=-1
    else:score_f=score/distance
    return score_f


def findPaths(G,node,length):
    #findPaths : returns all the permutations of paths of specifed length from a node
    #copié de : https://stackoverflow.com/questions/28095646/finding-all-paths-walks-of-given-length-in-a-networkx-graph
    if length==0:
        return [[node]]
    paths = [[node]+path for neighbor in G.neighbors(node) for path in findPaths(G,neighbor,length-1) if node not in path]  #MAGIC
    return paths


def get_best_path(list_of_paths,score_clusters):
    score_max=0
    best_path=[]
    for path in list_of_paths:
        score_path=get_score_path(path,score_clusters)
        if score_path> score_max:
            score_max=score_path
            best_path=path
    return best_path



def get_pos(POI_URI,df):
    return (df[df["URI_ID_du_POI"]==POI_URI]["Latitude"].item(),df[df["URI_ID_du_POI"]==POI_URI]["Longitude"].item())


def get_next_POI(current,current_position,df):
    df=df.copy()
    df["Coord"] = list(zip(df["Latitude"], df["Longitude"]))
    df["Distance_to_current"]=df["Coord"].apply(lambda point: hs.haversine(current_position, point))
    
    df["Score_ajuste"]=df.apply(lambda x: get_score_ajuste(x["Score"],x["Distance_to_current"]),axis =1)    
    next_poi_index=df["Score_ajuste"].idxmax()
    next_poi=df["URI_ID_du_POI"].loc[next_poi_index]
    t_visite=60
    return next_poi,t_visite

def get_itineraire(start,start_position,df):
    
    df_iti=df.copy()
    list_POI=[start]
    t,end_time=8.*60,19.5*60        # on commence l'itinéraire a 8h du matin et on finit l'itineraire a 19h30 
    current,current_position= start,start_position
    to_drop=df_iti.index[df_iti["URI_ID_du_POI"]==start].tolist()
    df_iti=df_iti.drop(to_drop)
    while t<end_time:
        next_POI,t_visite=get_next_POI(current,current_position,df_iti)
        list_POI.append(next_POI)
        t+=t_visite
        to_drop=df_iti.index[df_iti["URI_ID_du_POI"]==next_POI].tolist()
        df_iti=df_iti.drop(to_drop)
        #print(df_iti[df_iti["URI_ID_du_POI"]==next_POI])
    return list_POI
def get_global_itineraire(start,clustered,path):
    #input: start is the uuid of the POI 
    #       clustered is the dataset with k means 
    #       path is the path through the clusters
    
    itineraire = {}
    start_pos = get_pos(start,clustered)
    # position = (datatourisme_df[ datatourisme_df["URI_ID_du_POI"] == start ][ "Latitude" ].item() , datatourisme_df[ datatourisme_df["URI_ID_du_POI"] == start]["Longitude"].item())
    
    for day in range(len(path)):
        itineraire["day_"+str(day)]=get_itineraire(start,start_pos,df=clustered[clustered["Cluster"]==path[day]])
        start=itineraire["day_"+str(day)][-1]
        start_pos = get_pos(start,clustered)
    return itineraire

#Definition des paramètres d'itinéraires
MAX_TIME_PER_DAY = 480 #8h * 60 min

MAX_KM_BY_TRANSPORT = {
    "Marche": 5, #10 km Aller / Retour
    "Velo": 15, #30 km Aller / Retour
    "Voiture": 90 #180 km Aller / Retour
}
NUM_CLUSTER_BY_TRANSPORT={
    "Marche": 100, #10 km Aller / Retour
    "Velo": 50, #30 km Aller / Retour
    "Voiture": 30 #180 km Aller / Retour
}
# Gestion de la distance max


# Couleurs utilisées par folium pour les markers



FOLIUM_COLORS=[
    'red','blue', 'green', 'purple', 'orange', 'darkred',
    'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
    'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray'
]
# Zoom a appliquer sur la carte
ZOOM_LVL = {
    'Voiture': 8,
    'Velo': 11,
    'Marche': 20
}



# fonction de génération de graphes

def get_distances(pos,clusters):
    n= clusters.tolist().index(pos.tolist())
    distances=[(cluster,hs.haversine(pos,clusters[cluster])) for cluster in list(range(0,n)) + list(range(n+1, len(clusters)))]
    return distances

def get_neighbors(pos,clusters):
    distances=get_distances(pos,clusters)
    distances.sort(key = lambda x: x[1])
    return distances[:][:5]

def get_clustering(df,seed,num_clusters):    
    kmeans = KMeans(n_clusters=num_clusters,random_state=seed,n_init=50)
    X = df[['Latitude','Longitude']].values
    predictions = kmeans.fit_predict(X) 
    clustered = pd.concat([df.reset_index(), 
                        pd.DataFrame({'Cluster':predictions})], 
                        axis=1)
    return kmeans,predictions,clustered

def create_graph_and_clustering(df,num_clusters,seed=123):
    kmeans,predictions,clustered=get_clustering(df,num_clusters=num_clusters,seed=seed)
    G = nx.Graph()
    for k in range(len(kmeans.cluster_centers_)):
        G.add_node(k,pos= (kmeans.cluster_centers_[k][0],kmeans.cluster_centers_[k][1]))
    for k in range(len(kmeans.cluster_centers_)):
        five_closest=get_neighbors(kmeans.cluster_centers_[k],kmeans.cluster_centers_)
        for node in five_closest:
            G.add_edge(k,node[0])
    return G,kmeans,predictions,clustered

def get_first_cluster(clustered,u_start_poi_uuid):
    return clustered[clustered["URI_ID_du_POI"]==u_start_poi_uuid]["Cluster"].item()

def plot_markers(dataframe, map_to_plot, color_palette = FOLIUM_COLORS, icon='star'):
    """
        Plot markers on a foilum map using coord column on a dataframe and a specified color palette
    """
    max_colors_idx = len(color_palette) - 1

    for _idx, row in dataframe.iterrows():
        if _idx%5 ==1:
            color_idx = row["Jour"] - 1
            if color_idx > max_colors_idx:
                color_idx = color_idx % max_colors_idx
            color = color_palette[color_idx]
            icon_color = 'dimgray' if color == 'white' else 'white'
            folium.Marker(
                location= list(row.Coord),
                popup= f"<h5>Jour {row['Jour']}</h5><p>{row['Nom_du_POI']}</p>",
                icon= folium.Icon(color= color, icon_color= icon_color, icon=icon)
            ).add_to(map_to_plot)
        else: 
            pass



def get_user_radius_df(df,start_point,max_distance):
    app_df = df.copy()

    #Ensemble des coordonnées
    app_df["Coord"] = list(zip(app_df["Latitude"], app_df["Longitude"])) # Coord tupples

    # Calcul de la distance au point de départ
    app_df["Distance_start_point"] = app_df["Coord"].apply(lambda point: hs.haversine(start_point, point))
    
    # Conservation des points dans le rayon du point de départ du voyageur
    return app_df[app_df["Distance_start_point"] <= max_distance].copy()



def ajoute_coords(clustered):
    clustered["Coord"] = list(zip(clustered["Latitude"], clustered["Longitude"]))
    return clustered



def plot_itineraire(itineraire,df,map_to_plot,color_palette=FOLIUM_COLORS,icon='star'):
    for day in range(len(itineraire.keys())):
        trajet= itineraire[list(itineraire.keys())[day]]
        color_idx=day
        color = color_palette[color_idx]
        icon_color = 'dimgray' if color == 'white' else 'white'
        for idx_poi in range(len(trajet)):
            poi=trajet[idx_poi]
            nom=df[df["URI_ID_du_POI"]==poi]["Nom_du_POI"]
            folium.Marker(
                location= get_pos(poi,df),
                popup= f"<h5>Jour {day} , étape {idx_poi}</h5><p>{nom.item()}</p>",
                icon= folium.Icon(color= color, icon_color= icon_color, icon=icon)
                ).add_to(map_to_plot)


def setup():
    if exists("clean_data_w_coords.csv"):
        print("The first processing stage has already been done, using this data instead")
        datatourisme_df=pd.read_csv("clean_data_w_coords.csv")
    else:
        #this is the function to run first to get all the files already setup. takes like 5 minutes to run so its annoying. run once then run fast setup
        datatourisme_df,type_adapter=setup_dataframe()
        print("Pulled the data.")

        datatourisme_df=clean_latitude(datatourisme_df)
        print("Removed outliers")

        t1=time.time()
        datatourisme_df=create_categories(datatourisme_df,type_adapter)
        t2=time.time()
        datatourisme_df=datatourisme_df.drop(columns=["Categories_de_POI"])
        print("Created categories in",t2-t1,"seconds. Here are the categories  :\n",datatourisme_df.keys().tolist())

        datatourisme_df = ajoute_coords(datatourisme_df)
        datatourisme_df.to_csv("clean_data_w_coords.csv")
    # separates the hotel, restaurants and POI. 2 mins to run because unoptimised
    hotels,restaurants,datatourisme_df=separate_hotel_restaurants(datatourisme_df)
    hotels.to_csv("hotels.csv")
    restaurants.to_csv("restaurants.csv")
    datatourisme_df.to_csv("poi.csv")
    print("We now have",len(datatourisme_df),"POIs in our database")
# creates the following files :
# clean_data_w_coords.csv : POI + profil POI + coords POI , sans outliers 
# hotels.csv,restaurants.csv : on sépare les pois des hotels et restaurants
# poi.csv : what we need to do some clustering . POI + profil POI + score POI , sans outliers, sans hotels ni restaurants


def main_func(profil,u_start_poi_uuid,num_clusters,u_moyen_mobilite,u_nb_jour,seed=133):
    if exists("poi.csv") & exists("hotels.csv") & exists("restaurants.csv"):
        print("Extracting the data from already created files")
        pass
    else: 
        print("This is your first time running the code. This will take a couple minutes of setup at least")
        t1=time.time()
        setup()
        print("The setup took ",time.time()-t1," seconds")
    
    #num_clusters,u_start_poi_uuid,u_nb_jour = [] TODO
    
    datatourisme_df=pd.read_csv("poi.csv")
    u_start_point=get_pos(u_start_poi_uuid,datatourisme_df)
    print("Calculating POI scores based on user profile")
    datatourisme_df=calcule_score(datatourisme_df,profil)
    print("Clustering Point of Interests into small localities")
    G,kmeans,predictions,clustered=create_graph_and_clustering(datatourisme_df,num_clusters,seed=seed)
    print("Scoring localities")
    score_clusters=get_score_clusters(num_clusters,clustered)
    print("Navigating localities")
    start_cluster= get_first_cluster(clustered,u_start_poi_uuid)
    list_of_paths=findPaths(G,start_cluster,u_nb_jour-1)
    path_through_clusters=get_best_path(list_of_paths,score_clusters)
    print("We will go through the localities in the following order")
    print(path_through_clusters)
    print("Calculating itinerary")
    global_itineraire=get_global_itineraire(u_start_poi_uuid,clustered,path_through_clusters)
    print("DONE.")
    itineraire_map = folium.Map(location = u_start_point , tiles = "OpenStreetMap", zoom_start = ZOOM_LVL[u_moyen_mobilite])
    plot_itineraire(global_itineraire,clustered,itineraire_map,color_palette=FOLIUM_COLORS,icon='star')
    return clustered, path_through_clusters,global_itineraire,kmeans,predictions,G


