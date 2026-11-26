This README file was generated on 2026-10-22 by Håvard Steinshamn.
Last updated: 2026-10-26


-------------------
GENERAL INFORMATION
-------------------
// Title of Dataset: Field Experiments with Nitrogen fertilization levels to grass-clover leys with two seeding rates of red clover
// DOI: https://doi.org/10.18710/F5Z8BR
// Contact Information
     // Name: Håvard Steinshamn
     // Institution: NIBIO Norwegian Institue of Bioeconomy Research
     // Email: havard.steinshamn@nibio.no
     // ORCID: https://orcid.org/0000-0003-0052-7294

// Contributors: See metadata field Contributor.
// Data Type: See metadata field Data Type.
// Date of Collection: Experiments were conducted 2009-2013. Data were collected for this use in 2024 
// Geographic location: The geographical locations of experiments is given in the file EnvImpactBiorefine_exp.csv
// Funding sources: See metadata section Funding Information.

// Description of dataset: 
This data set represents results from eight factorial field experiments in grass-clover leys. The factors were nitrogen fertilization level and seeding rate of red clover. The data were used for assessing the climate impact and land use of processing the herbage in bioreinery, published in the journal Science of The Total Environment https://doi.org/10.1016/j.scitotenv.2025.180373     



--------------------------
METHODOLOGICAL INFORMATION
--------------------------
// Description of sources and methods used for collection/generation of data: 
A three-year factorial field experiment in grass-clover swards were conducted at eight locations in Norway between 2009 and 2013. Four locations were in Central Norway and four in Southern Norway. All plots were established with a mixture of timothy (Phleum pratense L., cv. ‘Grindstad’), meadow fescue (Lolium pratense Huds., cv. ‘Fure’)  and red clover (Trifolium pratense L., cv. ‘Reipo’). The experiment was arranged as a replicated split-plot design, with annual nitrogen (N) fertilisation rate (0, 80, 160 and 240 kg/ha) assigned to the main plots and the proportion of red clover in the seed mixture (low=10% and High=20% of a total seeding rate of 25 kg/ha) assigned to the subplots, with three replicates. In the low-clover treatment, timothy and meadow fescue constituted 65% and 25% of the total seeding rate, respectively, whereas the corresponding proportion in the high-clover treatment were 55% and 25%. Calcium ammonium nitrate was used as the N fertiliser. The annual N application was split between spring (37.5%), and after the first cut (37.5%), and after the second cut (25%). All plots received a phosphorus and potassium fertilizer (PK 5-17) in spring and potassium fertilizer (K47) after the first cut, at rates according to local recommendations. The first cut was taken at early heading stage of timothy, the second cut 500 growing degree days later (base temperature 0°C), and the third cut 600 growing degree days after the second. The chemical analysis was determined by near-infrared reflectance spectroscopy (NIRS) on samples pooled across the three replicates for each treatment, cut, location and year. Consequently, dry matter (DM) yield was averaged across the three replicates for each treatment and cut prior to statistical analysis. The proportion of clover in the DM was determined by NIRS. The data were analysed using linear mixed-effects models fitted with the lme4 package (Bates et al., 2924) in R (R Core team, 2024) using RStudio. The fixed effects were annual N fertilisation rate (0, 80, 120, 240 kg/ha), red clover proportion in the seed mixture (10 or 20%), and production year (first, second, or third year). Location and the interaction between location and production year were included as random effects. 


// Methods for processing the data: 

Processing of data is integrated in the section above



--------------------
DATA & FILE OVERVIEW
--------------------
// File List: 
00_README_EnvImpactBiorefine.txt
EnvImpactBiorefine_Exp.csv
EnvImpactBiorefine_Data.csv

// Relationship between files, if important: 
All files are data from the same experiment

// Is this an updated version of a dataset published on DataverseNO? yes/no
no


-----------------------------------------
DATA-SPECIFIC INFORMATION FOR: EnvImpactBiorefine_exp.csv
-----------------------------------------
// Variable/Column List: 
Exp_no- Location number of experiment (from 1 to 8)  
Region- Region of location ('1' for Southern Norway or '2' Central Norway)
Altitude- Altitude, meters above se level, of location
Soil type- Soil type class follwing the Norweagian classification, with clay content ranges: Sand<10%, silt<12%, silty light clay 12 < 25%, light clay 10 - <25 %, sandy clay, 25 - < 40% clay
Coordinates: coordinates for the experimental locations   
  
// Missing data codes: 
Not relevant
// Specialized formats or other abbreviations used: 
Not relevant

DATA-SPECIFIC INFORMATION FOR: EnvImpactBiorefine_data.csv
-----------------------------------------
// Variable/Column List: 
Exp_no- Location number of experiment (from 1 to 8)  
Region- Region of location ('1' for Southern Norway or '2' Central Norway)
No_cuts- Number of cuts per season
Est- calender year of esatblishment (seeding)
Prod_year- Production year after esatblishemnet ('1' for first year, '2' for second year, '3' for third year)
Clover_mix- Red clover proportion in the seed mixture ('10' for 10%, '20' for 20%)
N_rate- Annual nitrogen (N) fertiliser rate ('0' for 0 kg N, '8' for 80 kg N/ha, '16' for 160 kg N/ha, '24' for 240 kg N/ha)
Yield_cut1- Dry matter (DM) yield in the first cut in g/m2 
Yield_cut2-DM yield in the second cut in g/m2 
Yield_cut3-DM yield in the third cut in g/m2 
Tot_yield-Annual DM yield in g/m2 
CP_cut1- Crude protein (CP) conntent of the first cut herbage g/100g DM 
clover_cut1-Red clover proportion of the first cut herbage g/100g DM  
CP_cut2-Crude protein (CP) conntent of the second cut herbage g/100g DM 
clover_cut2-Red clover proportion of the second cut herbage g/100g DM  
CP_cut3-Crude protein (CP) conntent of the third cut herbage g/100g DM 
clover_cut3-Red clover proportion of the third cut herbage g/100g DM  
  
  
// Missing data codes: 
'.' is used for missing data

// Specialized formats or other abbreviations used: 
none


--------------------------
SHARING/ACCESS INFORMATION
--------------------------
// Licenses/Restrictions: See Terms tab.
// Links to publications that cite or use the data: See metadata field Related Publication.
// Links/relationships to related data sets: See metadata field Related Dataset.
// Data sources: See metadata field Data Source.
// Recommended citation: See citation generated by repository.


<
Acknowledgements. This README file template is adapted from the following documents/resources:

AJPS. ‘American Journal of Political Science Qualitative Data Verification Checklist’. Wiley, 11 March 2016. https://ajps.org/wp-content/uploads/2019/01/ajps-qualdata-checklist-ver-1-0.pdf.

Berkeley Library, University of California. How to Write a Good Documentation. Available at: http://guides.lib.berkeley.edu/how-to-write-good-documentation

Cornell University. Guide to writing "readme" style metadata. Available at: https://data.research.cornell.edu/content/readme#bestpractices

Corti, Louise, Veerle Van den Eynden, Libby Bishop, Matthew Woollard, Maureen Haaker, and Scott Summers. Managing and Sharing Research Data: A Guide to Good Practice. 2nd edition. Los Angeles: SAGE, 2019.

Dryad. Best practices for creating reusable data publications. Available at: https://datadryad.org/stash/best_practices#describe

PurpleBooth. A template to make good README.md. Available at: https://gist.github.com/PurpleBooth/109311bb0361f32d87a2

University of Bath. Working with data: Data Documentation and Metadata. Available at: https://library.bath.ac.uk/research-data/working-with-data/data-documentation-metadata

Zalando. Zalando's README Template. Available at: https://github.com/zalando/zalando-howto-open-source/blob/master/READMEtemplate.md#readme
>
