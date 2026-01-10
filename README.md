因为模型对于图像的两边长有被除数要求，为避免一般缩放产生形变而制作。

Because the model has a divisor requirement for the length of both sides of the image, it is made to avoid deformation caused by general scaling.



仓库中的节点使用时请直接将*.py文件拷贝到custom_node文件夹下即可，注意不要再在custom_node文件夹下建立新文件夹。可以直接下载也可以直接克隆仓库后拷贝进去。一般不会有依赖问题。
均为图片预处理节点。特点是保持原图的比例,不会产生轻微形变的同时，补出一些像素用来符合模型的边长要求。

To use a node in the repository, simply copy the *.py file to the custom_node folder. Be careful not to create a new folder within the custom_node folder. You can download it directly or clone the repository and copy it in. This generally doesn't cause dependency issues.
These are image preprocessing nodes. Their characteristic is that they maintain the original image's proportions without causing any slight deformation, while also adding some pixels to meet the model's side length requirements.

=====================================================================

节点img88.py，建立方便大模型处理的图片规格，两边都能被8整除的图片。对超大的图片可以缩小，图片像素量作为阈值。对于多出来的边缘，可以选择重复临近像素，黑底。可以继承遮罩。

The img88.py node creates image formats suitable for large models, ensuring that both sides are divisible by 8. Oversized images can be scaled down, using the pixel count as a threshold. For extra edges, adjacent pixels can be repeated, with a black background. Masks can be inherited.
<img width="1477" height="846" alt="image" src="https://github.com/user-attachments/assets/53e8e11d-adf5-4d6b-b706-d851af0b250d" />

=========================================================================

节点img8x.py：对输入图片的边长按照用户设置的乘数进行处理。处理后可以生成遮罩，方便后续处理。具体使用见配套流程：padimagewithimg8x.json

Node img8x.py: Processes the edge length of the input image according to the user-set multiplier. After processing, a mask can be generated to facilitate subsequent processing. Refer to the process: padimagewithimg8x.json
<img width="1608" height="826" alt="image" src="https://github.com/user-attachments/assets/1d0b697a-1690-46ad-ba2b-8239c00f3ad7" />

===========================================================================

上传一个流程padimagewithimg8x.json，用Flux fill来处理图片边长。基于fill扩图流程，可以迅速对图片做预处理。
如有需求请自行下载。
该流程说明：使用的是flux fill的inpaint方法，使用img8x.py节点对原图片进行边长放大处理后，生成对应空白部分的黑边，同时作为遮罩传出。
流程中红色节点为本img8x.py节点。
同时传出的还有扩图后的移动坐标，用来将原图贴回来。这样贴回来的图片就是用fill重写边缘但中心是原图的图片
可以在流程中保留fill扩大后的图，也可以保存重写边缘后的图。请自行更改节点。
===========================================================================
提供一个新节点：imgx8e.py。将flux，wan，qwen-image这三种模型的图片大小的官方预设值集成。方便文生图或者扩图时使用。

imgx8e.py. Integrates the official preset values for image sizes for the flux, wan, and qwen-image models. This is convenient for T2I or expanding images.

<img width="1179" height="782" alt="image" src="https://github.com/user-attachments/assets/a12e8526-1914-46d8-ac0a-374f43ec3b11" />

==========================================================================

提供一个将图片进行裁剪并缩放的节点:img8sc.py
将图片按照等比例缩放到**接近**目标宽高，达成效果：一边等于设定值，同时另一边超出设定值。设定值会根据用户的输入自行调整为能被8整除。
之后按照用户的选择进行裁剪。可以选择保留上部，下部，左部，右部，以及保留中间裁掉两边。见下图：
<img width="1828" height="707" alt="image" src="https://github.com/user-attachments/assets/98190874-eeec-4456-b003-3d497f8b23b9" />

==========================================================================

三个新节点方便qwen vqa用户反推与批量反推。具体用法请见配套流，如果需要批量处理，请安装ComfyUI-lumi-batcher并遵照该节点方法设置批处理。
img8_adv_image_loader.py按照文件夹载入图片，并输出qwen vqa接受的path数据路径。
img8txtsaver.py将反推内容保存进与图片相同的文件夹，或自行设定文件夹。
img8path2string.py将qwenvqa的path格式转换为正常的字符串path格式，同时可选输出文件名，方便使用。

具体用法参见配套流：打标未完成.jason。其中的红色节点为介绍中的节点。
另外：本人有 ComfyUI-Qwen3_VQA_enhanced用于替换qwen vqa原节点中的模型。具体请搜索仓库ComfyUI-Qwen3_VQA_enhanced

==========================================================================

llamachat.py：对节点组   https://github.com/lihaoyun6/ComfyUI-llama-cpp_vlm    的补充，增加了可以聊天（即扩写）的节点。ComfyUI中双击空白搜索：llama-cpp-chat。按图片连线即可。
<img width="1318" height="759" alt="image" src="https://github.com/user-attachments/assets/91dd1d45-5e06-414d-a17d-2f72ef6ca12d" />
