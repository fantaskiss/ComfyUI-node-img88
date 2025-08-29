因为模型对于图像的两边长有被除数要求，为避免一般缩放产生形变而制作。

Because the model has a divisor requirement for the length of both sides of the image, it is made to avoid deformation caused by general scaling.



仓库中的节点使用时请直接将*.py文件拷贝到custom_node文件夹下即可，注意不要再在custom_node文件夹下建立新文件夹。可以直接下载也可以直接克隆仓库后拷贝进去。一般不会有依赖问题。
均为图片预处理节点。特点是保持原图的比例,不会产生轻微形变的同时，补出一些像素用来符合模型的边长要求。

To use a node in the repository, simply copy the *.py file to the custom_node folder. Be careful not to create a new folder within the custom_node folder. You can download it directly or clone the repository and copy it in. This generally doesn't cause dependency issues.
These are image preprocessing nodes. Their characteristic is that they maintain the original image's proportions without causing any slight deformation, while also adding some pixels to meet the model's side length requirements.



节点img88.py，建立方便大模型处理的图片规格，两边都能被8整除的图片。对超大的图片可以缩小，图片像素量作为阈值。对于多出来的边缘，可以选择重复临近像素，黑底。可以继承遮罩。

The img88.py node creates image formats suitable for large models, ensuring that both sides are divisible by 8. Oversized images can be scaled down, using the pixel count as a threshold. For extra edges, adjacent pixels can be repeated, with a black background. Masks can be inherited.
<img width="1477" height="846" alt="image" src="https://github.com/user-attachments/assets/53e8e11d-adf5-4d6b-b706-d851af0b250d" />


节点img8x.py：对输入图片的边长按照用户设置的乘数进行处理。处理后可以生成遮罩，方便后续处理。具体使用见配套流程：padimagewithimg8x.json

Node img8x.py: Processes the edge length of the input image according to the user-set multiplier. After processing, a mask can be generated to facilitate subsequent processing. Refer to the process: padimagewithimg8x.json
<img width="1608" height="826" alt="image" src="https://github.com/user-attachments/assets/1d0b697a-1690-46ad-ba2b-8239c00f3ad7" />



上传一个流程padimagewithimg8x.json，用Flux fill来处理图片边长。基于fill扩图流程，可以迅速对图片做预处理。
如有需求请自行下载。
该流程说明：使用的是flux fill的inpaint方法，使用img8x.py节点对原图片进行边长放大处理后，生成对应空白部分的黑边，同时作为遮罩传出。
流程中红色节点为本img8x.py节点。
同时传出的还有扩图后的移动坐标，用来将原图贴回来。这样贴回来的图片就是用fill重写边缘但中心是原图的图片
可以在流程中保留fill扩大后的图，也可以保存重写边缘后的图。请自行更改节点。

提供一个新节点：imgx8e.py。将flux，wan，qwen-image这三种模型的图片大小的官方预设值集成。方便文生图或者扩图时使用。

imgx8e.py. Integrates the official preset values for image sizes for the flux, wan, and qwen-image models. This is convenient for T2I or expanding images.

<img width="1179" height="782" alt="image" src="https://github.com/user-attachments/assets/a12e8526-1914-46d8-ac0a-374f43ec3b11" />
