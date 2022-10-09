# -*- coding: utf-8 -*-
'''

Customized Processing Tool Script: Convert csv to shp and merge into a single vector layer
Author: Zulfadli Mawardi, S3915436 RMIT University

'''

from qgis.PyQt.QtCore import QCoreApplication, QVariant, QDateTime
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterNumber,
                       QgsCoordinateReferenceSystem,
                       QgsVectorLayer,
                       QgsPointXY,
                       QgsProject,
                       QgsFeature,
                       QgsGeometry,
                       QgsVectorFileWriter,
                       QgsWkbTypes,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterFile,
                       QgsField,
                       QgsFields,
                       QgsProcessingUtils)
from qgis import processing
import os
import datetime

class CSVToSHPProcessingAlgorithm(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    SOURCE_FOLDER = 'SOURCE_FOLDER'
    SELECT_LYR = 'SELECT_LYR'
    SUFFIX = 'SUFFIX'
    OUTPUT = 'OUTPUT'

    def tr(self, string):

        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CSVToSHPProcessingAlgorithm()

    def name(self):

        return 'Convert and Merge'

    def displayName(self):

        return self.tr('Convert and Merge')

    def group(self):

        return self.tr('Custom scripts')

    def groupId(self):

        return 'customscript'

    def shortHelpString(self):

        return self.tr("This is a customized Processing Tool script made to convert\
        one or more csv files in a folder to shapefile(s) and merge the shapefiles grouped by\
        the suffix on the file name into a single shapefile.\n\
        \n\
        Select the source folder. The algorithm will read the folder path\
        and read any csv files in the same folder.\n\
        \n\
        The user will be able to set the coordinate reference system (CRS) for the\
        converted shapefile. The default CRS will be EPSG:4326, the commonly used WGS84 for GPS\
        map projection.\n\
        \n\
        The suffix can be set by the user to group the files accordingly. The default suffix is\
        empty and will merge all the shapefiles into a single vector layer in the mapview.\n\
        The final output of this algorithm will be a single vector layer file containing all\
        the points based on the coordinates in the csv file.\n\
        The time field assuming to be in the last 6 fields are converted from the Unix\
        Epoch time format into the dd-mm-yyyy HH:MM:SS format and added to the new columns\n\
        \n\
        Please refer to https://epsg.io/ for other CRS ID. The CRS ID\
        can be identified as 'EPSG:__ID__'.\
         ")

    def initAlgorithm(self, config=None):


        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFile(
                self.SOURCE_FOLDER,
                self.tr("Source folder"),
                behavior=QgsProcessingParameterFile.Folder)
            )
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.SELECT_LYR,
                self.tr('Selection layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.SUFFIX,
                self.tr('Suffix'),
                defaultValue='',
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):
        
        def isfloat(num):
            try:
                float(num)
                return True
            except ValueError:
                return False
        
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source_folder = self.parameterAsString(
            parameters,
            self.SOURCE_FOLDER,
            context
        )
        
        sel_lyr = self.parameterAsVectorLayer(
            parameters,
            self.SELECT_LYR,
            context
        )

        suffix = self.parameterAsString(
            parameters,
            self.SUFFIX,
            context
        )
        
        # Setting variable to contain field name for latitude and longitude
        lon_field = 'Longitude'
        lat_field = 'Latitude'
        
        # Set coordinate reference system
        spatRef = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
 
        # Get folder path
        
        fileDir = source_folder
        fileList = os.listdir(fileDir)

        
        # Create a layer for the csv file and get the column headings
        csv_file = QgsVectorLayer(fileDir+'\\'+fileList[0], fileList[0][:-4], 'ogr')
        csvFileData = csv_file.dataProvider()
        fields = csvFileData.fields()
        
        newFields = QgsFields()
        vals = csv_file.getFeature(fid=1).attributes()
        for v in range(len(vals)):
            if isfloat(vals[v]):
                newFields.append(QgsField(fields[v].name(), QVariant.Double))
            else:
                newFields.append(QgsField(fields[v].name(), QVariant.String))
        
        # Add new field for converted time
        for i in range(1,7):
            newFields.append(QgsField('T'+str(i)+'_CONVERTED', QVariant.DateTime))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            newFields,
            1,
            spatRef
        )
        
        # Create an empty list to store features to be merged
        feats = []
        count = 0
        total = len(fileList)
        
        # Running the algorithm for every file in the source folder
        for file in fileList:
            if file[-3:] == 'csv':
                # Filter files by suffix
                if file[:-4].endswith(suffix):
                # Assign file basename to a variable
                    filename_ = file[:-4]
                
                    # Create a layer for the csv file and get the column headings
                    csv_file = QgsVectorLayer(fileDir+'\\'+filename_+'.csv', filename_, 'ogr')
                    count = count+1
                    
                    
                    
                    # Reads every row/feature in the csv file
                    for feat in csv_file.getFeatures():
                        
                        # Add the table values to the tmeporary layer
                        attrs = feat.attributes()
                    
                        pt = QgsPointXY()
                        outFeature = QgsFeature()
                        
                        # Add the table values to the tmeporary layer
                        attrs = feat.attributes()
                        
                        for k in range(len(attrs)):
                            if isfloat(attrs[k]):
                                attrs[k]=float(attrs[k])
                        
                        # Converting time values from Unix Epoch time format to dd-mm-yyyy datetime format
                        for i in range(-7,-1):
                            timediv = float(attrs[-7])/1000
                            if timediv >= 1642636800 and timediv <= 1649116799:
                                timediv = timediv
                            else:
                                timediv = 0
                                
                            ptDateTime = QDateTime.fromSecsSinceEpoch(timediv)
                            attrs.append(ptDateTime)
                        
                        outFeature.setAttributes(attrs)
                    
                        # Create point geometry features using the coordinates from the csv file and add to the temporary layer
                        pt.setX(float(feat[lon_field]))
                        pt.setY(float(feat[lat_field]))
                        outFeature.setGeometry(QgsGeometry.fromPointXY(pt))
                        sink.addFeature(outFeature)
                        
                    # Update the progress bar
                    feedback.setProgress(int(count * total))
        

        
        # Send some information to the user
        feedback.pushInfo('CRS is {4326}')
        

        return {self.OUTPUT:dest_id}
