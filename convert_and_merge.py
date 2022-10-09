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
                       QgsProcessingParameterEnum,
                       QgsCoordinateReferenceSystem,
                       QgsVectorLayer,
                       QgsPointXY,
                       QgsProject,
                       QgsFeature,
                       QgsGeometry,
                       QgsProcessingParameterFile,
                       QgsField,
                       QgsFields,
                       QgsProcessingUtils,
                       QgsFeatureRequest)
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
        From the sample datasets the example of suffixes are:\n\
        1. Vodafone_-_9C65F933984C_DataRate_Agg\n\
        2. Telstra_-_9C65F9339DE8_DataRate_Agg\n\
        3. Optus_-_9C65F9339228_DataRate_Agg\n\
        \n\
        Characteristics of the dataset to be accepted by this algorithm:\
        1. The last 7 fields to the 2nd last field contains Unix Epoch timestamp\
        2. Start date of observation (stored in the 6 time fields) starts from 20-Jan-22 to 04-Apr-22\n\
        3. the csv file only contains a single pair of xy coordinate per row\
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
                [QgsProcessing.TypeVectorPolygon],
                optional=True
            )
        )


        self.addParameter(
            QgsProcessingParameterEnum(
                self.SUFFIX,
                self.tr('Suffix options'),
                options=['Vodafone_-_9C65F933984C_DataRate_Agg','Telstra_-_9C65F9339DE8_DataRate_Agg','Optus_-_9C65F9339228_DataRate_Agg'],
                #default='',
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

        suffix = self.parameterAsInt(
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
        csv_base = QgsVectorLayer(fileDir+'\\'+fileList[0], fileList[0][:-4], 'ogr')
        csvbaseData = csv_base.dataProvider()
        fields = csvbaseData.fields()
        
        newFields = QgsFields()
        vals = csv_base.getFeature(fid=1).attributes()
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
        
        #Create a temporary layer to store feature points and add the field names
        temp_layer = QgsVectorLayer('Point','default output','memory')
        temp_layer_data = temp_layer.dataProvider()
        temp_layer_data.addAttributes(newFields)
        temp_layer.updateFields()
        
        # Create an empty list to store features to be merged
        feats = []
        count = 0
        total = len(fileList)
        
        Suffixes = {0:'Vodafone_-_9C65F933984C_DataRate_Agg',1:'Telstra_-_9C65F9339DE8_DataRate_Agg',2:'Optus_-_9C65F9339228_DataRate_Agg'}
        if suffix is not None:
            suffix = Suffixes[suffix]
        else:
            suffix = ''
            
        # Running the algorithm for every file in the source folder
        for file in fileList:
            if file[-3:] == 'csv':
                # Filter files by suffix                
                if file[:-4].endswith(''):
                # Assign file basename to a variable
                    filename_ = file[:-4]
                
                    # Create a layer for the csv file and get the column headings
                    csv_file = QgsVectorLayer(fileDir+'\\'+filename_+'.csv', filename_, 'ogr')
                    csv_base = QgsVectorLayer(fileDir+'\\'+fileList[0], fileList[0][:-4], 'ogr')
                    csvbaseData = csv_base.dataProvider()
                    fields = csvbaseData.fields()
                    
                    newFields = QgsFields()
                    vals = csv_base.getFeature(fid=1).attributes()
                    for v in range(len(vals)):
                        if isfloat(vals[v]):
                            newFields.append(QgsField(fields[v].name(), QVariant.Double))
                        else:
                            newFields.append(QgsField(fields[v].name(), QVariant.String))
                    
                    # Add new field for converted time
                    for i in range(1,7):
                        newFields.append(QgsField('T'+str(i)+'_CONVERTED', QVariant.DateTime))
                    
                    # Reads every row/feature in the csv file
                    for feat in csv_file.getFeatures():
                        
                        # Add the table values to the tmeporary layer
                        attrs = feat.attributes()
                    
                        pt = QgsPointXY()
                        outFeature = QgsFeature()
                        
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
                        temp_layer_data.addFeature(outFeature)
                        count = count+1
                    # Update the progress bar
                    feedback.setProgress(int(count * total))
        
        QgsProject.instance().addMapLayer(temp_layer)
        
        # Select points in the polygon
        if sel_lyr is not None:
            sel_par = {"INPUT":temp_layer,"PREDICATE":6,"INTERSECT":sel_lyr,"METHOD":0,"OUTPUT":dest_id}
            SelOut_Lyr = processing.run('qgis:selectbylocation',sel_par)
        
            # Create a new layer with the selected point features
            new_layer = SelOut_Lyr['OUTPUT'].materialize(QgsFeatureRequest().setFilterFids(SelOut_Lyr['OUTPUT'].selectedFeatureIds()))
        else:
            new_layer = temp_layer
        # Transfer the selected feature to sink layer
        
        for f in new_layer.getFeatures():
            sink.addFeature(f)
        
        # Send some information to the user
        feedback.pushInfo('CRS is {4326}')
        
        return {self.OUTPUT:temp_layer.featureCount()}
