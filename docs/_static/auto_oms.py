import os
from omsdetector import MofCollection
from mai.adsorbate_constructor import adsorbate_constructor

mofs_path = os.getcwd() #path to folder of CIFs
oms_data_path = mofs_path #path to store the OMS results
ads_species = 'O' #adsorbate species
bond_length = 1.75 #desired distance between OMS and ads_species

#Run the Open Metal Detector
mof_coll = MofCollection.from_folder(collection_folder=mofs_path,
	analysis_folder=oms_data_path)
mof_coll.analyse_mofs()

#add adsorbate for every CIF in mofs_path
for file in os.listdir(mofs_path):
	if '.cif' not in file:
		continue
	mof_path = os.path.join(mofs_path,file)
	ads = adsorbate_constructor(ads_species,bond_length)
	new_mof_atoms = ads.get_adsorbate(mof_path)