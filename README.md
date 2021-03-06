# Archive-Tools
This repository has some utility scripts used for searching and downloading data from various providers.

ALOS-2:

1. auig2_download.py - Command line download of data from AUIG2.  Eliminates the need to log into the Web/Silverlight interface to download your orders

SENTINEL-1:

1. scihub_dl.py - Download a product from SciHub given the product id
2. scihub_archive.py - More robust script to create a local database of SciHub products, search that database with a shapefile or WKT geometry, and download products.  You will need GDAL python bindings for this to work.

TerraSAR-X:
Useful scripts for downloading data from DLR, comparing TDX acquisitions with tasking orders, and KML of orders and aquired data 

1. compare_tdx_plan.py - This will compare the ASCII from [EOWEB](https://centaurus.caf.dlr.de:8443/eoweb-ng/template/default/welcome/entryPage.vm) with the TanDEM-X_Acquisition_Timeline found under the Investigator tab on the [DLR Science Service System](http://sss.terrasar-x.dlr.de/) for conflicts with your tasking orders.  You will need to download the Excel spreadsheet and save it as a CSV.
2. eoweb_ascii2kml.py - This will create a KML from the ASCII from [EOWEB](https://centaurus.caf.dlr.de:8443/eoweb-ng/template/default/welcome/entryPage.vm) for tasking orders and search results.
3. download_dlr_ftp.py - This script downloads data for your proposals from DLR's FTP.  This requires Python 2.7+
4. infoterra2kml.py - This searches the [TerraSAR-X Archive](http://terrasar-x-archive.infoterra.de/) using a WKT geometry and creates a KML of the results.
