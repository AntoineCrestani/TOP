
import networkx as nx
import haversine as hs
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
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

#0-> walk, 1->bikes, 2->vehicles
#t->MAX_KM_BY_TRANSPORT, c->NUM_CLUSTER_BY_TRANSPORT, z->ZOOM_LVL

TRANSPORT_CONSTS = [
    {"t": 5, "c": 100, "z": 20}, 
    {"t": 15, "c": 30, "z": 11}, 
    {"t": 90, "c": 10, "z": 8} 
] 

class Itinerary_ML():
    def __init__(self, df_pois, user_profile, seed=123):
        u_id = user_profile["u_id"]
        print("Starting the clustering process")
        self.df = df_pois
        self.start_pos = self.get_pos_w_id(u_id, self.df)
        # calculating POI scores based on the user profile 
        print(user_profile["profile"])
        self.df = self.weight_pois(user_profile["profile"])

        u_transport = user_profile["u_tr_type"] #car,bike,walk
        t_vals = TRANSPORT_CONSTS[0 if u_transport=="walk" else 1 if u_transport=="bike" else 2]
        # number of clusters, depends on the transportation ( more clusters = less surface to cover per cluster)
        self.num_clusters = t_vals["c"]
        self.G, self.kmeans, self.predictions, self.clustered = self.create_graph_and_clustering(seed)
        print("Clustering done")

        #calculating the mean score of a cluster
        self.score_clusters = self.get_score_clusters()
        # finding the cluster of our start point
        self.start_cluster = self.get_first_cluster(u_id)
        
        u_days = int(user_profile["u_nb_days"])
        # generating the complete list of paths of length u_days -1 that start from the beginning. TODO : improve this ...
        self.list_of_paths = self.find_paths(self.G, self.start_cluster, u_days-1)
        #best path is the path with the best mean score.
        self.path_through_clusters = self.get_best_path()
        print("Found the best path through the cluster")
        self.global_itineraire = self.get_global_itineraire(u_id)
        print("Here is the itinerary:\n")
        print(self.global_itineraire)

    def get_pos_w_id(self, id_poi, df):
        return (df[df["id"]==id_poi]["lat"].item(),df[df["id"]==id_poi]["long"].item())

    def weight_pois(self, profile_vals):
        self.df["score"] = self.df[ADJUSTED_TYPES].dot(profile_vals)
        return self.df

    def get_distances(self, pos, clusters):
        n = clusters.tolist().index(pos.tolist())
        distances = [(cluster, hs.haversine(pos, clusters[cluster])) for cluster in list(range(0, n)) + list(range(n+1, len(clusters)))]
        return distances

    def get_neighbors(self, pos, clusters, nb_closest):
        distances = self.get_distances(pos, clusters)
        distances.sort(key = lambda x: x[1])
        return distances[:][:nb_closest]

    def get_clustering(self, seed):    
        kmeans = KMeans(
            n_clusters = self.num_clusters,
            random_state=seed,
            n_init=50
        )
        X = self.df[['lat','long']].values
        predictions = kmeans.fit_predict(X) 
        clustered = pd.concat(
            [
                self.df.reset_index(), 
                pd.DataFrame({'Cluster':predictions})
            ], 
            axis = 1
        )
        return kmeans, predictions, clustered

    def create_graph_and_clustering(self, seed):
        kmeans, predictions, clustered = self.get_clustering(seed)
        G = nx.Graph()
        for k in range(len(kmeans.cluster_centers_)):
            G.add_node(
                k, 
                pos = (
                    kmeans.cluster_centers_[k][0], 
                    kmeans.cluster_centers_[k][1]
                )
            )
        for k in range(len(kmeans.cluster_centers_)):
            five_closest = self.get_neighbors(
                kmeans.cluster_centers_[k], 
                kmeans.cluster_centers_, 
                5
            )
            for node in five_closest:
                G.add_edge(k, node[0])
        return G, kmeans, predictions, clustered

    def get_score_clusters(self):
        #returns the mean score of all clusters
        scores = []
        for c in range(self.num_clusters):
            cluster = self.clustered[self.clustered["Cluster"]==c]
            scores.append((c, cluster["score"].mean()))
        return scores

    def get_first_cluster(self, poi_id):
        return self.clustered[self.clustered["id"]==poi_id]["Cluster"].item()

    def find_paths(self, G, node, length):
        #findPaths : returns all the permutations of paths of specifed length from a node
        #copié de : https://stackoverflow.com/questions/28095646/finding-all-paths-walks-of-given-length-in-a-networkx-graph
        if length==0:
            return [[node]]
        paths = [[node]+path for neighbor in G.neighbors(node) for path in self.find_paths(G,neighbor,length-1) if node not in path]  #MAGIC
        return paths

    def get_score_path(self, path):
        #returns the score of a path
        return sum([self.score_clusters[node][1] for node in path])

    def get_best_path(self):
        score_max = 0
        best_path = []
        for path in self.list_of_paths:
            score_path = self.get_score_path(path)
            if score_path > score_max:
                score_max = score_path
                best_path = path
        return best_path

    def get_score_ajuste(self, score, distance):
        # returns the adjusted score for a POI . TO REMAKE
        # TODO IMPROVE this GREATLY. We had ideas with amey. A step function would be nice
        if distance < 0.01:
            return -1
        else:
            return score/distance

    def get_next_POI(self, current, current_position, df):
        df = df.copy()
        df["Coord"] = list(zip((df["lat"]), df["long"]))
        df["Distance_to_current"] = df["Coord"].apply(lambda point: hs.haversine(current_position, point))
        
        df["Score_ajuste"] = df.apply(lambda x: self.get_score_ajuste(x["score"], x["Distance_to_current"]), axis = 1)
   
        next_poi_index = df["Score_ajuste"].idxmax()
        next_poi = df["id"].loc[next_poi_index]
        t_visite = 60
        return next_poi, t_visite

    def get_itineraire(self, start, start_position, df):
    
        df_iti = df.copy()
        list_POI = [start]
        t, end_time = 8.*60, 19.5*60        # on commence l'itinéraire a 8h du matin et on finit l'itineraire a 19h30 
        current, current_position = start, start_position
        to_drop = df_iti.index[df_iti["id"]==start].tolist()
        df_iti = df_iti.drop(to_drop)
        while t < end_time and len(df_iti)>=1:
            next_POI, t_visite = self.get_next_POI(current, current_position, df_iti)
            list_POI.append(next_POI)
            t += t_visite
            to_drop = df_iti.index[df_iti["id"]==next_POI].tolist()
            df_iti = df_iti.drop(to_drop)
        return list_POI

    def get_global_itineraire(self, poi_id):
        #input: start is the uuid of the POI 
        #       clustered is the dataset with k means 
        #       path is the path through the clusters
        
        itineraire = {}
        start_pos = self.start_pos
        # position = (datatourisme_df[ datatourisme_df["URI_ID_du_POI"] == start ][ "Latitude" ].item() , datatourisme_df[ datatourisme_df["URI_ID_du_POI"] == start]["Longitude"].item())
        start = poi_id
        for day in range(len(self.path_through_clusters)):
            itineraire["day_"+str(day)] = self.get_itineraire(start, start_pos, df = self.clustered[self.clustered["Cluster"]==self.path_through_clusters[day]])
            start = itineraire["day_"+str(day)][-1]
            start_pos = self.get_pos_w_id(start, self.clustered)
        return itineraire
