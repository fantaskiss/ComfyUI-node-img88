如简介所说，建立方便大模型处理的图片规格，两边都能被8整除的图片。对超大的图片可以缩小，图片像素量作为阈值。可以选择重复临近像素，黑底。可以继承遮罩。
据说ComfyUI以及各种模型适合处理8的倍数的变长的图片，我也不知道是不是真的，先来一个吧。
感谢deepseek的辛勤编写。如有bug请自行处理。


新上传了PadImageForOutpaintingSimplified.py
这也是一个节点，所不同的是它是按照两边都能被64整除做的。同样是因为有这么个传言，64整除的更好被各种模型处理。
同时上传一个流程，用kontext来处理分辨率比较小的图片。基于扩图流程做的，加上这个节点可以迅速对图片做预处理。
如有需求请自行下载。

该流程说明：使用的是kontext的inpaint节点，本PadImageForOutpaintingSimplified.py节点对原图片进行边长放大处理后，生成对应空白部分的黑边，同时作为遮罩传出。
同时传出的还有扩图后的移动坐标，用来将原图贴回来。这样贴回来的图片就是用kontext重写边缘但中心是原图的图片
可以在流程中保留kontext扩大后的图，也可以保存重写边缘后的图。请自行更改节点。


提供一个新的节点:img8x.py 具有PadImageForOutpaintingSimplified.py的所有功能，所不同的是，可以对边长的倍数人为设置。
<img width="1608" height="826" alt="image" src="https://github.com/user-attachments/assets/1d0b697a-1690-46ad-ba2b-8239c00f3ad7" />

提供一个新节点：imgx8e.py。将flux，wan，qwen-image这三种模型的图片大小的官方预设值集成。方便文生图或者扩图时使用。
<img width="1179" height="782" alt="image" src="https://github.com/user-attachments/assets/a12e8526-1914-46d8-ac0a-374f43ec3b11" />
