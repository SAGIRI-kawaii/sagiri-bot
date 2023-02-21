from dataclasses import dataclass, Field


@dataclass
class Text2Image(object):
    prompt: str
    negative_prompt: str
    prompt_style: str = "None"
    prompt_style2: str = "None"
    steps: int = 20
    restore_faces: bool = False
    tiling: bool = False
    n_iter: int = 1
    batch_size: int = 1
    cfg_scale: float = 12.0
    seed: int = -1
    subseed: int = -1
    subseed_strength: int = 0
    seed_resize_from_h: int = 0
    seed_resize_from_w: int = 0
    height: int = 512
    width: int = 512
    enable_hr: bool = True
    scale_latent: bool = True
    denoising_strength: float = 0.7


@dataclass
class Image2Image(object):
    prompt: str
    negative_prompt: str
    init_images: list[str]
    prompt_style: str = "None"
    prompt_style2: str = "None"
    init_img_with_mask: None = None
    init_mask: None = None
    mask_mode: None = None
    steps: int = 20
    mask_blur: int = 0
    inpainting_fill: int = 0
    restore_faces: bool = False
    tiling: bool = False
    n_iter: int = 1
    batch_size: int = 1
    cfg_scale: float = 12.0
    seed: int = -1
    subseed: int = -1
    denoising_strength: float = 0.7
    seed_resize_from_h: int = 0
    seed_resize_from_w: int = 0
    height: int = 512
    width: int = 512
    resize_mode: int = 0
    upscaler_index: int = 0
    upscale_overlap: int = 0
    inpaint_full_res: bool = False
    inpainting_mask_invert: int = 0
    include_init_images: bool = True


DEFAULT_NEGATIVE_PROMPT = "lowers, bad anatomy, bad hands, text, error, missing fingers, " + \
                          "extra digit, fewer digits, cropped, worst quality, low quality, " + \
                          "normal quality, jpeg artfacts, signature, watermark, username, blurry, " + \
                          "bad feet, multiple breasts, (mutated hands and fingers:1.5 ), (long body " + \
                          ":1.3), (mutation, poorly drawn :1.2) , black-white, bad anatomy, " + \
                          "liquid body, liquid tongue, disfigured, malformed, mutated, anatomical " + \
                          "nonsense, text font ui, error, malformed hands, long neck, blurred, " + \
                          "lowers, lowres, bad anatomy, bad proportions, bad shadow, uncoordinated " + \
                          "body, unnatural body, fused breasts, bad breasts, huge breasts, " + \
                          "poorly drawn breasts, extra breasts, liquid breasts, heavy breasts, " + \
                          "missing breasts, huge haunch, huge thighs, huge calf, bad hands, " + \
                          "fused hand, missing hand, disappearing arms, disappearing thigh, " + \
                          "disappearing calf, disappearing legs, fused ears, bad ears, poorly drawn " + \
                          "ears, extra ears, liquid ears, heavy ears, missing ears, fused animal " + \
                          "ears, bad animal ears, poorly drawn animal ears, extra animal ears, " + \
                          "liquid animal ears, heavy animal ears, missing animal ears, text, ui, " + \
                          "error, missing fingers, missing limb, fused fingers, one hand with more " + \
                          "than 5 fingers, one hand with less than 5 fingers, one hand with more " + \
                          "than 5 digit, one hand with less than 5 digit, extra digit, fewer digits, " + \
                          "fused digit, missing digit, bad digit, liquid digit, colorful tongue, " + \
                          "black tongue, cropped, watermark, username, blurry, JPEG artifacts, " + \
                          "signature, 3D, 3D game, 3D game scene, 3D character, malformed feet, " + \
                          "extra feet, bad feet, poorly drawn feet, fused feet, missing feet, " + \
                          "extra shoes, bad shoes, fused shoes, more than two shoes, poorly drawn " + \
                          "shoes, bad gloves, poorly drawn gloves, fused gloves, bad cum, " + \
                          "poorly drawn cum, fused cum, bad hairs, poorly drawn hairs, fused hairs, " + \
                          "big muscles, ugly, bad face, fused face, poorly drawn face, cloned face, " + \
                          "big face, long face, bad eyes, fused eyes poorly drawn eyes, extra eyes, " + \
                          "malformed limbs, more than 2 nipples, missing nipples, different nipples, " + \
                          "fused nipples, bad nipples, poorly drawn nipples, black nipples, " + \
                          "colorful nipples, gross proportions. short arm, (((missing arms))), " + \
                          "missing thighs, missing calf, missing legs, mutation, duplicate, morbid, " + \
                          "mutilated, poorly drawn hands, more than 1 left hand, more than 1 right " + \
                          "hand, deformed, (blurry), disfigured, missing legs, extra arms, " + \
                          "extra thighs, more than 2 thighs, extra calf, fused calf, extra legs, " + \
                          "bad knee, extra knee, more than 2 legs, bad tails, bad mouth, " + \
                          "fused mouth, poorly drawn mouth, bad tongue, tongue within mouth, " + \
                          "too long tongue, black tongue, big mouth, cracked mouth, bad mouth, " + \
                          "dirty face, dirty teeth, dirty pantie, fused pantie, poorly drawn pantie, " + \
                          "fused cloth, poorly drawn cloth, bad pantie, yellow teeth, thick lips, " + \
                          "bad cameltoe, colorful cameltoe, bad asshole, poorly drawn asshole, " + \
                          "fused asshole, missing asshole, bad anus, bad pussy, bad crotch, " + \
                          "bad crotch seam, fused anus, fused pussy, fused anus, fused crotch, " + \
                          "poorly drawn crotch, fused seam, poorly drawn anus, poorly drawn pussy, " + \
                          "poorly drawn crotch, poorly drawn crotch seam, bad thigh gap, " + \
                          "missing thigh gap, fused thigh gap, liquid thigh gap, poorly drawn thigh " + \
                          "gap, poorly drawn anus, bad collarbone, fused collarbone, " + \
                          "missing collarbone, liquid collarbone, strong girl, obesity, " + \
                          "worst quality, low quality, normal quality, liquid tentacles, " + \
                          "bad tentacles, poorly drawn tentacles, split tentacles, fused tentacles, " + \
                          "missing clit, bad clit, fused clit, colorful clit, black clit, " + \
                          "liquid clit, QR code, bar code, censored, safety panties, " + \
                          "safety knickers, beard, furry ,pony, pubic hair, mosaic, excrement, " + \
                          "faeces, shit, futa, testis"
