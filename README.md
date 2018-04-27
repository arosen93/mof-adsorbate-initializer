# MOF Adsorbate Initializer (MAI)
Python code to initialize the position of adsorbates on MOFs for high-throughput DFT screening workflows

## Setup
1. MAI requires Python 3.x. If you do not already have Python installed, the easiest option is to download the [Anaconda](https://www.anaconda.com/download/) distribution.
2. Install the most recent versions of Pymatgen and ASE. This can be easily done using `pip install pymatgen ase` 
3. Download or clone the MAI repository and run `pip install .` from the MAI base directory.
4. (recommended) To detect open metal sites (OMSs), download and install [Zeo++](http://www.zeoplusplus.org/download.html) (any version >= 0.3). By default, Zeo++'s OMS detection algorithm does not output a lot of information necessary to add adsorbates to OMSs. To address this, copy `network.cc` from `network/network.cc` in the MAI directory and replace the corresponding `network.cc` file in the base directory of Zeo++ before installation. The relevant changes can be found starting on line 1165.
5. (recommended) To generate energy grids for the adsorption of molecular adsorbates (**`Todo`**)

## Ready-to-Run Examples
The main use of MAI is to add a single-atom adsorbate or a molecular adsorbate to a given adsorption site on a MOF. Sample scripts are provided in `/examples` that can be used to: 1) add a CH4 adsorbate to an O adsorption site using a RASPA-generated energy grid (`add_CH4.py`); 2) add an O adsorbate to an OMS using Zeo++'s OMS detection algorithm (`add_O.py`); 3) add an H adsorbate to an O adsorption site using one of Pymatgen's nearest neighbor algorithms (`add_H.py`).

## adsorbate_constructor
The main tool to initialize adsorbate positions is the `adsorbate_constructor`, as described below:
```python
class adsorbate_constructor():
	"""
	This class constructs an ASE atoms object with an adsorbate
	"""
	def __init__(self,ads_species,bond_dist,site_species=None,site_idx=None,
		r_cut=2.5,sum_tol=0.5,rmse_tol=0.25,overlap_tol=0.75):
		"""
		Initialized variables

		Args:
			ads_species (string): string of atomic element for adsorbate (e.g. 'O')
			
			bond_dist (float): distance between adsorbate and surface atom. If
			used with get_adsorbate_raspa, it represents the maximum distance
			for the adsorbate from the surface atom
			
			site_species (string): string of atomic element for the adsorption
			site species. not needed when calling get_adsorbate_zeo_oms
			
			site_idx (int): ASE index for the adsorption site (defaults to
			the last element of element type site_species). not needed when
			calling get_adsorbate_zeo_oms
			
			r_cut (float): cutoff distance for calculating nearby atoms when
			ranking different adsorption sites
			
			sum_tol (float): threshold to determine planarity. when the sum
			of the Euclidean distance vectors of coordinating atoms is less
			than sum_tol, planarity is assumed
			
			rmse_tol (float): second threshold to determine planarity. when the 
			root mean square error of the best-fit plane is less than rmse_tol,
			planarity is assumed
			
			overlap_tol (float): distance below which atoms are assumed to be
			overlapping so that the structure can be flagged as erroneous
		"""
```
Once the `adsorbate_constructor` is instanced, one of three routines can be called: `get_adsorbate_raspa`, `get_adsorbate_pm`, and `get_adsorbate_zeo_oms`. These are described below.

## Molecular Adsorbates
The `get_adsorbate_raspa` function is used to add a molecular adsorbate to the adsorption site of a MOF based on a molecular mechanics energy grid generated by the molecular simulation program RASPA, and the molecular adsorbate is initialized in the lowest energy position within some cutoff distance from the proposed adsorption site. It currently only supports CH4 adsorption but can be readily extended to support other molecular adsorbates. The `get_adsorbate_raspa` function is described below:

```python
def get_adsorbate_raspa(self,atoms_filepath,grid_path=None,
	write_file=True,new_mofs_path=None,error_path=None):
	"""
	This function adds a molecular adsorbate based on an energy grid
	generated using RASPA

	Args:
		atoms_filepath (string): filepath to the structure file (accepts
		CIFs, POSCARs, and CONTCARs)
		
		grid_path (string): path to the directory containing RASPA energy
		grids (defaults to /energy_grids within the directory of the
		starting structure files)
		
		write_file (bool): if True, the new ASE atoms object should be
		written to a CIF file (defaults to True)
		
		new_mofs_path (string): path to store the new CIF files if
		write_file is True (defaults to /new_mofs within the
		directory of the starting structure files)
		
		error_path (string): path to store any adsorbates flagged as
		problematic (defaults to /errors within the directory of the
		starting structure files)
	Returns:
		new_atoms (Atoms object): ASE Atoms object of MOF with adsorbate
		
		new_name (string): name of MOF with adsorbate
	"""
```
The script below is taken from `examples/add_CH4.py`. It reads in CIF files from `mof_path`, adds CH4 within 3.0 Å of the last O atom in the CIF file (ensuring none of the atoms in CH4 overlap within 1.3 Å of the MOF), and stores the new CIF files with CH4 adsorbate in `new_mofs_path`. It assumes that the RASPA-generated energy grids are located in a folder named `examples/oxygenated_MOFs/energy_grids` since `grid_path` is not set in `get_adsorbate_raspa`. 

```python
import os
from mai.adsorbate_constructor import adsorbate_constructor

mof_path = 'examples/oxygenated_MOFs/'
new_mofs_path = 'examples/add_CH4/'
max_dist = 3.0
overlap_tol = 1.3
mol_species = 'CH4'
site_species = 'O'
for filename in os.listdir(mof_path):
	filepath = os.path.join(mof_path,filename)
	ads_const = adsorbate_constructor(mol_species,max_dist,
		site_species=site_species,overlap_tol=overlap_tol)
	mof_adsorbate, mof_name = ads_const.get_adsorbate_raspa(filepath,
		new_mofs_path=new_mofs_path)
```
![AHOKIR_CH4](test/success/add_CH4/ahokir_ch4.png)
## Atomic Adsorbates
There are two implemented methods of initializing atomic adsorbates. The first allows for the use of Zeo++'s OMS detection and Voronoi tesselation algorithms. The second allows for the use of one of Pymatgen's nearest neighbor algorithms.

### Using Zeo++ OMS detection
The `get_adsorbate_zeo_oms` function is used to add an atomic adsorbate to the OMS of a MOF using data generated from Zeo++. The `get_adsorbate_zeo_oms` function is described below:

```python
def get_adsorbate_zeo_oms(self,atoms_filepath,oms_data_path=None,
	write_file=True,new_mofs_path=None,error_path=None):
	"""
	This function adds an adsorbate to each unique OMS in a given
	structure. In cases of multiple identical OMS, the adsorbate with
	fewest nearest neighbors is selected. In cases of the same number
	of nearest neighbors, the adsorbate with the largest minimum distance
	to extraframework atoms (excluding the adsorption site) is selected.

	Args:
		atoms_filepath (string): filepath to the structure file (accepts
		CIFs, POSCARs, and CONTCARs)
		
		oms_data_path (string): path to the Zeo++ open metal site data
		containing .oms and .omsex files (defaults to /oms_data within the
		directory of the starting structure files)
		
		write_file (bool): if True, the new ASE atoms object should be
		written to a CIF file (defaults to True)
		
		new_mofs_path (string): path to store the new CIF files if
		write_file is True (defaults to /new_mofs within the
		directory of the starting structure files)
		
		error_path (string): path to store any adsorbates flagged as
		problematic (defaults to /errors within the directory of the
		starting structure files)
	Returns:
		new_atoms_list (list): list of ASE Atoms objects with an adsorbate
		added to each unique OMS
		
		new_name_list (list): list of names associated with each atoms
		object in new_atoms_list
	"""
```
The script below is taken from `examples/add_O.py`. It reads in CIF files from `mof_path`, adds an O atom 2.0 Å away from an OMS in the CIF file (ensuring that the O adsorbate doesn't overlap within 1.3 Å of the MOF), and stores the new CIF files with O adsorbate in `new_mofs_path`. It assumes that the Zeo++ `.oms` and `.omsex` files are stored in a folder named `examples/bare_MOFs/oms_data` since `oms_data_path` is not set in `get_adsorbate_zeo_oms`. Note that neither `site_species` or `site_idx` should be specified for `get_adsorbate_zeo_oms` since the algorithm identifies the adsorption OMS from Zeo++.

```python
import os
from mai.adsorbate_constructor import adsorbate_constructor

mof_path = 'examples/bare_MOFs/'
new_mofs_path = 'examples/add_O/'
ads_species = 'O'
bond_length = 2.0
overlap_tol = 1.3

for filename in os.listdir(mof_path):
	filepath = os.path.join(mof_path,filename)
	ads_const = adsorbate_constructor(ads_species,bond_length,
		overlap_tol=overlap_tol)
	mof_adsorbate_list, mof_name_list = ads_const.get_adsorbate_zeo_oms(filepath,
		new_mofs_path=new_mofs_path)
```
![azixud_O](test/success/add_O/azixud_o.png)
### Using Pymatgen NN algorithms
The `get_adsorbate_pm` function is used to add an atomic adsorbate to specified site of a MOF using data generated from Pymatgen's `local_env` structural environment class. The `get_adsorbate_pm` function is described below:


```python
def get_adsorbate_pm(self,atoms_filepath,NN_method='vire',write_file=True,
	new_mofs_path=None,error_path=None):
	"""
	Use Pymatgen's nearest neighbors algorithms to add an adsorbate

	Args:
		atoms_filepath (string): filepath to the structure file (accepts
		CIFs, POSCARs, and CONTCARs)
		
		NN_method (string): string representing the desired Pymatgen
		nearest neighbor algorithm (options include 'vire','voronoi',
		'jmol','min_dist','okeeffe','brunner', and 'econ')
		
		write_file (bool): if True, the new ASE atoms object should be
		written to a CIF file (defaults to True)
		
		new_mofs_path (string): path to store the new CIF files if
		write_file is True (defaults to /new_mofs within the
		directory of the starting structure files)
		
		error_path (string): path to store any adsorbates flagged as
		problematic (defaults to /errors within the directory of the
		starting structure files)
	Returns:
		new_atoms (Atoms object): ASE Atoms object of MOF with adsorbate
		
		new_name (string): name of MOF with adsorbate
	"""
```
The script below is taken from `examples/add_H.py`. It reads in CIF files from `mof_path`, adds an H atom 1.0 Å away from the last O atom in the CIF file (ensuring that the H adsorbate doesn't overlap within 0.75 Å of the MOF), and stores the new CIF files with H adsorbate in `new_mofs_path`. It uses the Valence Ionic Radius Evaluator (VIRE) nearest-neighbor algorithm implemented in Pymatgen to determine the geometry of the coordination environment. Note that `get_adsorbate_pm` can be used to add atoms to an OMS as well if desired, so long as the ASE index of the OMS is specified in `adsorbate_constructor`.
```python
import os
from mai.adsorbate_constructor import adsorbate_constructor

mof_path = 'examples/oxygenated_MOFs/'
new_mofs_path = 'examples/add_H/'
site_species = 'O'
ads_species = 'H'
bond_length = 1.0
NN_method = 'vire'

for filename in os.listdir(mof_path):
	filepath = os.path.join(mof_path,filename)
	ads_const = adsorbate_constructor(ads_species,bond_length,
		site_species=site_species)
	mof_adsorbate, mof_name = ads_const.get_adsorbate_pm(filepath,NN_method,
		new_mofs_path=new_mofs_path)
```
![anugia_oh](test/success/add_H/anugia_oh.png)
## External Tools
### Running RASPA for Generating Energy Grids
`Todo`
### Running Zeo++ for OMS Detection
Zeo++ is the recommended method for detecting OMSs in combination with MAI. To use the Zeo++ OMS detection algorithm, one simply has to run `.../zeo++-0.3/network -omsex filepath`, where `-omsex` requests OMS detection with extended output, and `filepath` is the path to the CIF file of the MOF. This will produce a `.oms` and `.omsex` file for each MOF, which must be stored if MAI is to be used to add adsorbates to the OMSs.
