仓库中的节点使用时请直接将*.py文件拷贝到custom_node文件夹下即可，注意不要再在custom_node文件夹下建立新文件。可以直接下载也可以直接克隆仓库后拷贝进去。一般不会有依赖问题。
均为图片预处理节点。特点是保持原图的比例进行边长缩放，不会产生轻微形变。

节点img88.py，建立方便大模型处理的图片规格，两边都能被8整除的图片。对超大的图片可以缩小，图片像素量作为阈值。对于多出来的边缘，可以选择重复临近像素，黑底。可以继承遮罩。
<img width="1477" height="846" alt="image" src="https://github.com/user-attachments/assets/53e8e11d-adf5-4d6b-b706-d851af0b250d" />


节点img8x.py：对输入图片的边长按照用户设置的乘数进行处理。处理后可以生成遮罩，方便后续处理。
<img width="1608" height="826" alt="image" src="https://github.com/user-attachments/assets/1d0b697a-1690-46ad-ba2b-8239c00f3ad7" />

上传一个流程padimagewithimg8x.json，用kontext来处理分辨率比较小的图片。基于扩图流程做的，可以迅速对图片做预处理。
如有需求请自行下载。
该流程说明：使用的是kontext的inpaint方法，使用img8x.py节点对原图片进行边长放大处理后，生成对应空白部分的黑边，同时作为遮罩传出。
流程中红色节点为本img8x.py节点。
同时传出的还有扩图后的移动坐标，用来将原图贴回来。这样贴回来的图片就是用kontext重写边缘但中心是原图的图片
可以在流程中保留kontext扩大后的图，也可以保存重写边缘后的图。请自行更改节点。

提供一个新节点：imgx8e.py。将flux，wan，qwen-image这三种模型的图片大小的官方预设值集成。方便文生图或者扩图时使用。
<img width="1179" height="782" alt="image" src="https://github.com/user-attachments/assets/a12e8526-1914-46d8-ac0a-374f43ec3b11" />
