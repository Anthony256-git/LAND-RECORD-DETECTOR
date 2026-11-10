import pandas as pd
import math


def check_plot_numbers(cadastral_data, survey_data):
    cadastral_plot_numbers = set(cadastral_data['Plot_Number'])
    survey_plot_numbers = set(survey_data['Plot_Number'])
    
    missing_in_survey = cadastral_plot_numbers - survey_plot_numbers
    missing_in_cadastral = survey_plot_numbers - cadastral_plot_numbers
    
    return missing_in_survey, missing_in_cadastral   

def check_duplicate_coordinates(data):
    duplicate_coordinates = data[data.duplicated(subset=['Northing', 'Easting'], keep=False)]
    return duplicate_coordinates

def calculate_plot_areas(data):

    results = []

    # Group coordinates according to plot number
    for plot_number, plot_data in data.groupby('Plot_Number', sort=False):

        eastings = plot_data['Easting'].tolist()
        northings = plot_data['Northing'].tolist()

        area = 0

        # Apply the Shoelace Formula
        for i in range(len(eastings)):

            next_point = (i + 1) % len(eastings)

            area += (
                eastings[i] * northings[next_point]
                - eastings[next_point] * northings[i]
            )

        # Convert square metres to hectares
        area = abs(area) / 2
        area_hectares = area / 10000

        results.append({
            'Plot Number': plot_number,
            'Calculated Area (Ha)': area_hectares
        })

    return pd.DataFrame(results)

def compare_areas(cadastral_areas, survey_areas):

    # Match plots in both datasets
    comparison = pd.merge(
        cadastral_areas,
        survey_areas,
        on='Plot Number',
        how='inner'
    )

    # Calculate area difference
    comparison['Difference (Ha)'] = abs(
        comparison['Calculated Area (Ha)_x']
        - comparison['Calculated Area (Ha)_y']
    )

    # Calculate percentage disagreement
    comparison['Difference (%)'] = (
        comparison['Difference (Ha)']
        / comparison['Calculated Area (Ha)_x']
    ) * 100

    return comparison

def compare_coordinates(cadastral_data, survey_data):
    results = []

    common_plots = set(cadastral_data['Plot_Number']) & set(survey_data['Plot_Number'])

    for plot in common_plots:
        official = cadastral_data[cadastral_data['Plot_Number'] == plot]
        survey = survey_data[survey_data['Plot_Number'] == plot]

        official_points = list(zip(official['Easting'], official['Northing']))
        survey_points = list(zip(survey['Easting'], survey['Northing']))

        used_points = []
        distances = []

        # Find the naersest survey point for each official point
        for e1, n1 in official_points:
            nearest_distance = float('inf')
            nearest_index = -1

            for i, (e2, n2) in enumerate(survey_points):
                if i not in used_points:
                    distance = math.sqrt((e2 - e1) ** 2 + (n2 - n1) ** 2)
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_index = i

            if nearest_index != -1:
                used_points.append(nearest_index)
                distances.append(nearest_distance)

        if distances:
            average_distance = sum(distances) / len(distances)
            max_distance = max(distances)

            results.append({"Plot Number": plot, "Average Distance (m)":\
                             average_distance, "Max Distance (m)": max_distance
                             ,"Points Compared": len(distances),"Unmatched official Points": len(official_points) - len(distances),
                             "Unmatched survey Points": len(survey_points) - len(distances)})


            return pd.DataFrame(results)

def run_analysis(cadastral_data, survey_data):
    # Check plot numbers
    missing_in_survey, missing_in_cadastral = check_plot_numbers(cadastral_data, survey_data)

    # Check for duplicate coordinates
    cadastral_duplicates = check_duplicate_coordinates(cadastral_data)
    survey_duplicates = check_duplicate_coordinates(survey_data)

    # Calculate areas
    cadastral_areas = calculate_plot_areas(cadastral_data)
    survey_areas = calculate_plot_areas(survey_data)

    # Compare areas
    area_results = compare_areas(cadastral_areas, survey_areas)

    # Compare coordinates
    comparison_results = compare_coordinates(cadastral_data, survey_data)

    return(
        missing_in_survey,
        missing_in_cadastral,
        cadastral_duplicates,
        survey_duplicates,
        area_results,
        comparison_results
    )