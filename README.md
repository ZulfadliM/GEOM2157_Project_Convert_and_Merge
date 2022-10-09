# Geospatial Programming Major Project: Convert and Merge

Created by: Zulfadli Mawardi, S3915436

A major project assignment in lieu of the GEOM2157 Geospatial Programming course in RMIT University

This is a customized Processing Tool script made to convert
one or more csv files in a folder to shapefile(s) and merge the shapefiles grouped by
the suffix on the file name into a single shapefile.

Select the source folder. The algorithm will read the folder path
and read any csv files in the same folder.

From the sample datasets the example of suffixes are:
1. Vodafone_-_9C65F933984C_DataRate_Agg
2. Telstra_-_9C65F9339DE8_DataRate_Agg
3. Optus_-_9C65F9339228_DataRate_Agg

Characteristics of the dataset to be accepted by this algorithm:
1. The last 7 fields to the 2nd last field contains Unix Epoch timestamp
2. Start date of observation (stored in the 6 time fields) starts from 20-Jan-22 to 04-Apr-22
3. the csv file only contains a single pair of xy coordinate per row

Output layer added to the map is the final output layer.
