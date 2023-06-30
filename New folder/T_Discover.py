import csv
import re
import os
import pandas as pd
import networkx as nx
from tqdm import tqdm
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

def process_data(df, range1_low, range1_high, range2_low, range2_high, range3_low, range3_high, range4_low, range4_high):
    file_df = df
    unique_count = df['Report Name'].nunique()

    def bag_of_words_generation(x):
        j = {}
        for i in x:
            m = {}
            m[i[1]] = 1
            j[i[0]] = m
        for i in x:
            j[i[0]][i[1]] = 1
        return pd.DataFrame(j).T

    kpi_list = file_df[["Report Name", "Dimensions Used/KPI/Metric Used"]].values.tolist()
    unique_count = file_df['Report Name'].nunique()
    print("Number of unique values:", unique_count)
    bow_dimensions = bag_of_words_generation(kpi_list).fillna(0)
    bow_dimensions.columns = bow_dimensions.columns.astype(str)

    def perform_clustering(bag_of_words):
        temp_bag_of_words = bag_of_words.copy()
        kmeans_final = KMeans(n_clusters=15)
        kmeans_final.fit(temp_bag_of_words)
        temp_bag_of_words.insert(loc=0, column='cluster_labels', value=kmeans_final.labels_)
        return temp_bag_of_words

    bag_of_words_with_cluster_label = perform_clustering(bow_dimensions)

    similarity_df = cosine_similarity(bow_dimensions)
    report_names = bow_dimensions.index.tolist()

    def prepare_final_output(df, report_names, bag_of_words_with_cluster_label):
        csv_file = []
        for r_index, row in enumerate(df):
            for c_index in range(r_index, len(row)):
                if r_index != c_index:
                    csv_file.append([report_names[r_index], report_names[c_index], df[r_index][c_index] * 100])
        csv_df = pd.DataFrame(csv_file)
        csv_df.columns = ["report_a", "report_b", "score"]

        bag_of_words_with_cluster_label_new = bag_of_words_with_cluster_label.copy()
        bag_of_words_with_cluster_label_new["report_name"] = bag_of_words_with_cluster_label_new.index
        bag_of_words_with_cluster_label_new = bag_of_words_with_cluster_label_new[["report_name", "cluster_labels"]]
        bag_of_words_with_cluster_label_new.columns = ["r_report_name", "r_cluster_labels"]

        Similarity_df = pd.merge(left=csv_df, right=bag_of_words_with_cluster_label_new, how="inner",
                                 left_on="report_a", right_on="r_report_name")
        bag_of_words_with_cluster_label_compared = bag_of_words_with_cluster_label.copy()
        bag_of_words_with_cluster_label_compared["report_name"] = bag_of_words_with_cluster_label_compared.index

        bag_of_words_with_cluster_label_compared = bag_of_words_with_cluster_label_compared[
            ["report_name", "cluster_labels"]]
        bag_of_words_with_cluster_label_compared.columns = ["c_report_name", "c_cluster_labels"]
        Similarity_df = pd.merge(left=Similarity_df, right=bag_of_words_with_cluster_label_compared, how="inner",
                                 left_on="report_b", right_on="c_report_name")

        Similarity_df = Similarity_df[["report_a", "report_b", "score", "r_cluster_labels", "c_cluster_labels"]]
        Similarity_df = Similarity_df.query('r_cluster_labels == c_cluster_labels')
        Similarity_df.columns = ["Report Name(A)", "Compared Report Name(B)", "Similarity Score", "Cluster(A)",
                                 "Cluster(B)"]
        csv_df.to_csv(r"C:/Users/sunny.chandel/Desktop/T-Discover/output_T_Discover/similarity_subset.csv")
        return csv_df

    Similarity_df = prepare_final_output(similarity_df, report_names, bag_of_words_with_cluster_label)

    Similarity_df = Similarity_df.rename(columns={'Report Name(A)': 'report_a',
                                                  'Compared Report Name(B)': 'report_b',
                                                  'Similarity Score': 'score'})

    def group_reports(df):
        G = nx.Graph()

        for _, row in df.iterrows():
            report_a = row['report_a']
            report_b = row['report_b']
            G.add_edge(report_a, report_b)

        groups = list(nx.connected_components(G))
        group_report_pairs = []
        for i, group in enumerate(groups):
            for report in group:
                group_report_pairs.append((f"Group {i + 1}", report))

        group_report_df = pd.DataFrame(group_report_pairs, columns=['Group', 'Report'])
        group_report_df.drop_duplicates(subset='Report', keep='first', inplace=True)
        group_report_df.reset_index(drop=True, inplace=True)

        return group_report_df

    df_similarity = Similarity_df

    # Group reports based on the score ranges
    df_score_threshold_1 = df_similarity[(df_similarity['score'] >= range1_low) & (df_similarity['score'] <= range1_high)]
    df_score_threshold_1 = df_score_threshold_1[['report_a', 'report_b']]
    df_score_threshold_1 = group_reports(df_score_threshold_1)
    df_score_threshold_1 = df_score_threshold_1.rename(columns={f'{range1_low}-{range1_high}': 'score'})

    df_score_threshold_2 = df_similarity[(df_similarity['score'] > range2_low) & (df_similarity['score'] <= range2_high)]
    df_score_threshold_2 = df_score_threshold_2[['report_a', 'report_b']]
    df_score_threshold_2 = group_reports(df_score_threshold_2)
    df_score_threshold_2 = df_score_threshold_2.rename(columns={f'{range2_low}-{range2_high}': 'score'})

    df_score_threshold_3 = df_similarity[(df_similarity['score'] > range3_low) & (df_similarity['score'] <= range3_high)]
    df_score_threshold_3 = df_score_threshold_3[['report_a', 'report_b']]
    df_score_threshold_3 = group_reports(df_score_threshold_3)
    df_score_threshold_3 = df_score_threshold_3.rename(columns={f'{range3_low}-{range3_high}': 'score'})

    df_score_threshold_4 = df_similarity[(df_similarity['score'] > range4_low) & (df_similarity['score'] <= range4_high)]
    df_score_threshold_4 = df_score_threshold_4[['report_a', 'report_b']]
    df_score_threshold_4 = group_reports(df_score_threshold_4)
    df_score_threshold_4 = df_score_threshold_4.rename(columns={f'{range4_low}-{range4_high}': 'score'})

    df_not_in_threshold_3 = df[~df['Report Name'].isin(df_score_threshold_3['Report'])][
    ['Report Name', 'Dimensions Used/KPI/Metric Used']]

    print(df_not_in_threshold_3)

    df_not_in_threshold_4 = df[~df['Report Name'].isin(df_score_threshold_4['Report'])][
    ['Report Name', 'Dimensions Used/KPI/Metric Used']]
    print(df_not_in_threshold_4)

    df_not_in_threshold_3_4 = pd.concat([df_not_in_threshold_3, df_not_in_threshold_4])



   

    return df_score_threshold_1, df_score_threshold_2, df_score_threshold_3, df_score_threshold_4, df_not_in_threshold_4,unique_count
