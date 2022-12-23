# AnalyZr
- AnalyZr is designed for the shape analysis of zircon grains in resin mounts, photographed under reflected and transmitted light.
- Thirteen shape parameters are measured: area, equivalent diameter, perimeter, minor axis, major axis, solidity, convex area, form factor, roundness, compactness, aspect ratio, maximum Feret diameter, minimum Feret diameter.
- AnalyZr uses .png images.

## Run the Software
- A zipped folder is available for Windows and Ubuntu on this repository. You can find the latest release on the right of your screen under 'Releases', alternatively navigate to: https://github.com/TarynScharf/AnalyZr/releases
- Download the latest release and unzip to use. The unzipped folder contains all the files that AnalyZr will need to run. 
- Find the AnalyZr.exe file in the unzipped folder and double-click on it to start the application.
- A window will pop up showing the outputs of AnalyZr starting up. After a few seconds AnalyZr will open.

## Data Capture
### Load Files for Data Capture
- The image analysis procedure starts with data capture.
- Open the Data Capture menu and select Load Images. This opens the "Select Images for Spot Capture" dialog.
- Next to "Data Capture Image Folder", browse for a folder where your images are stored.
- Inside your folder, the image files MUST be named according to the following convention:
sampleID_filename_imagetype.
  - sampleID: usually numeric
  - filename: any unique name of your choice
  - filetype: reflected light (RL) e.g. S1_abc_RL
  - filetype: transmitted light(TL) e.g. S1_abc_TL 
  - filetype: collage (nothing) e.g. S1_abc 
  - IMPORTANT: sampleID comes fist, image type comes last, everything is separated with underscores
 - Tick "load jsons separately" if you keep the corresponding json files in a different folder to your images.
 - If you have no json files, one will be made for every image in the folder. There MUST be a json file for each data capture image.
 - If you have no json files, you can tick "Generate json files if missing". If you don't tick this, and json files are missing, you will be asked if you want to create the missing json files.
 - You cannot data capture without a json file.

### Capture Data
- The images will display and you are able to scroll through them using the left and right arrow key on the keyboard, or the Data Capture/Move to Next Image and Data Capture/Move to Previous Image commands.
- Capture analytical spot locations and ID's using Data Capture/Capture Analytical Spot, or the "s" key as a short cut.
- Whilst capturing an analytical spot, you can select a CL texture from a drop down both and capture free form text notes related to analytical spot.
- You MUST capture a scale in order to measure the zircons:
  - If a linear scale is present on the photo, capture it with Data Capture/Capture Scale or the "l" key shortcut. You'll be asked to specify the length of the scale.
  - If no linear scale is present, you can approximate scale from the size of analytical spots that you have placed on your image. Use Data Capture/Capture Analytical Spot Size to draw a bounding box around a spot. The axes of all spot bounding boxes across all images related to the sample will be averaged to arrive at an average spot diameter. This average is done because hand-marked spots are inaccurate. Spot diameters are currently assumed to be 30 micrometers in diameter, which is a  working average for secondary ionization analysis when no more precise scale is available.
  - Linear scales will always be given preference. Try not to capture both scale types in your images.
 - If you want to mark an object for deletion, use Data Capture/Mark Object for Deletion. For historical reasons, this command currently lets your draw a rectangle. Draw it INSIDE the object you want to remove. Examples: grains duplicated across images, grains that aren't zircons etc.
 - All this information is written to the json files.
 - Even if you have no analytical spots to capture, you MUST complete data capture for two reasons:
   - To capture a scale. No scale = no measurements.
   - To create json files if you have none.
 
## Segment Images
### Binarise Images
- Once you've captured your data, convert them into black and white binary images.
- Open Segment Images/Image Segmentation Toolbox. This opens the "Image Segmentation Toolbox" dialog.
- In the "Visual References" box, browse and select your RL and TL images.
  - Select which of the images to binarise. 
  - Binarising both reflected light (RL) & transmitted light(TL) gives best results.
    - Binarising RL only will work under the following conditions:
      - There is sufficient contrast between your background and foreground. If not, binarisation will return failed results (usually picks up the image border)
      - There are no zircons forming closed clusters. If there are closed clusters, the fill routine will fill the spaces between the closed-clustered zircons.
    - Binarising TL only should pick up the zircon boundaries, but you'll have to remove unwanted internal contours
- Click to create the binary image. Red grain contours are displayed on top of your original images.
- You can switch between the RL and TL background image by clicking on the relevant "Display" button in the Visual References box.
- You can save the binary image as a .png by clicking on Save Mask. When you save the image, the file path is written to the json file, thus a json file is required to save an image. The system will locate the json file in the json folder. If no json folder has been selected, you will be prompted to load the json folder. Load the json folder using Segment Images/Load Json Files.
- You might want to change the grain boundaries automatically presented.
  - You can remove any contours by right-clicking on them. Contours will display in yellow when you hover over them. 
  - As small objects (area < 1/6th of largest object in the image) are automatically removed before measurement, therefore you need not worry about cleaning up small unwanted objects.
  - You can undo your contour deletion by clicking on the "Undo Delete Contour" button.
  - You can draw a new boundary by clicking on the "Grain Boundary Capture" button, or using the "p" key shortcut. Proceed to digitise your new boundary. A polygon will be drawn as you digitise. Right-click when you are done drawing your new polygon. Everything inside the polygon will be added to the image as a grain. You can also touch up existing boundaries using this tool e.g. fill a hole inside a grain, extend an existing boundary.
- Once you have binarised images, the Image Segmentation section of the Image Segmentation Toolbox will become available for use.

### Image Segmentation
- To automatically separate grains, click on the "Separate Grains" button in the Segment Images box of the Image Segmentation Toolbox. 
  - The image will update to display the grain boundaries coloured for angle. Bright spots show the highly concave points along the grains. Note that only those contours on which nodes (potential points of contact) are detected, are displayed. 
  - Points of high concavity that represent potential points of contact (nodes) are shown in red.
  - Break lines are two-point lines that separate grains. They are displayed on top of your image in red and connect two nodes.
    - You can delete unwanted break lines by right clicking on them. They will display in yellow if you hover over them.
    - You can digitise a new break line by clicking on the "Draw Break Line" button.
    - Once you are happy with the break lines, click on the "Save Changes" button. This will update the image to reflect the grain separation.
- You might want to change the grain boundaries presented.
  - You can remove any contours by right-clicking on them.
  - You can undo your contour deletion by clicking on the "Undo Delete Contour" button.
  - You can draw a new boundary by clicking on the "Grain Boundary Capture" button, or using the "p" key shortcut. Proceed to digitise your new boundary. A polygon will be drawn as you digitise. Middle-click when you are done drawing your new polygon. Everything inside the polygon will be added to the image as a grain. You can also touch up existing boundaries using this tool e.g. fill a hole inside a grain, extend an existing boundary.
- You can save the binary image as a .png by clicking on Save Mask. When you save the image, the file path is written to the json file, thus a json file is required to save an image. The system will locate the json file in the json folder. If no json folder has been selected, you will be prompted to load the json folder. Load the json folder using Segment Images/Load Json Files.

## Measure Shapes
- If you have just binarised and segmented your image, you can move straight to shape measurement by clicking on the "Measure Shapes" button in the Measure Shapes box.
- If you want to measure a pre-existing image that you have already saved, browse and load the file in the "Browse for Mask Image" window.
- If you want to measure multiple images in one go, browse and load your folder of mask images in the "Process Mask Folder" window. The masks will display and you are able to scroll through them using the left and right arrows on the key board.
- Measure shapes by clicking on the "Measure" button.
  - The image will update with the following removed: boundary objects, objects less than 1/6th the size of the largest object in the image, objects you marked for deletion during data capture.
  - The remaining, measured objects have red boundaries and are numbered. 
  - Analytical spots are shown in green. You can reposition spots using the "Reposition Spot" button.
  - A table will pop up with all of your measurements. You can save the table to a .csv file or push to a database.
  - IMPORTANT: If you want to push to a database, the system is currently designed for a Microsoft Access database, and will assume the following:
    - You have the database set up. You will be prompted to browse for the database.
    - Your database contains a table called "import_shapes"
    - Your table contains the following fields: sampleid, image_id, grain_number, grain_centroid, grain_spots, area, equivalent_diameter, perimeter, minor_axis, major_axis, solidity, convex_area, formFactor, roundness, compactness, aspectRatio, minFeret, maxFeret, contour, image_dimensions, mask_image.
   -IMPORTANT: of there are any holes in your grains, AnalyZr will fill them. 
   -If you are measuring shapes in a single image, an image will be produced showing your grains, their numbers, and associated spots. Unfortunately this functionality has not yet been extended to batch processing of a folder. 
## Test Data
- Test data is provided in the test_data folder. Two cases are provided:
  - RL_TL: Measuring shapes from a RL and TL image. A RL and TL images are provided in the RL_TL folder.
  - Collage: Measuring shapes from a collage image. A collage image is a single image comprised of several photos. The user is required to capture the image boundaries. It is assumed that this is done in a software like VOTT. Both the collage image and associated json file with image boundaries is provided in the folder.
    - Often hand-written notes may be written anywhere on the original collage image, thus data capture is performed on the original collage image. The "source file" subfolder contains the original collage image and json file, for data capture.
    - Individual RL and TL images are required for binarisation. The RL and TL images have been extracted from the collage image, and have the same extents in pixels. RL and TL images are provided in the RL_TL_extracts folder.

## Citation
- To be updated.
