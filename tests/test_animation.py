from copy import deepcopy

from hcaptcha_bridge.capture import same_pixels, selected_animation, static_samples, temporal_snapshot


def samples():
    frames = []
    for phase in range(8):
        pixels = [[230,230,230] for _ in range(10000)]
        for y in range(40,49):
            for x in range(40,49):
                pixels[y*100+x] = [100+phase%2*50,80,70]
        frames.append(dict(question="Click the circle",canvases=[dict(x=0,y=100,width=1000,height=800)],
                           tiles=[],references=[],prompt=None,box=dict(width=520,height=570),sample=pixels,image=str(phase)))
    return frames


def test_learned_animation_keeps_fixed_pixels_guarded():
    frames=samples()
    assert not static_samples(frames)
    learned=temporal_snapshot(frames)
    assert learned and len(learned["temporal_frames"]) <= 5
    next_frame=deepcopy(frames[0])
    next_frame["sample"][44*100+44]=[240,150,190]
    assert same_pixels(learned,next_frame)
    next_frame["sample"][80*100+80]=[0,0,0]
    assert not same_pixels(learned,next_frame)
    assert not temporal_snapshot(frames[:-1]+[next_frame])


def test_no_whole_scene_mask_or_layout_changes():
    frames=samples()
    frames[1]["sample"]=[[0,0,0] for _ in range(10000)]
    assert temporal_snapshot(frames) is None
    frames=samples()
    frames[-1]["question"]="Click a different animal"
    assert temporal_snapshot(frames) is None


def test_selected_marker_is_anchored_without_expanding_animation():
    frames=samples(); learned=temporal_snapshot(frames)
    after=deepcopy(frames[-1])
    after["sample"][44*100+53]=[0,0,240]
    assert not same_pixels(learned,after)
    assert same_pixels(learned,after,[[440,440]])
    selected=selected_animation(learned,after,[[440,440]],[])
    assert same_pixels(selected,after)
    assert selected["animation"]["moving"] == learned["animation"]["moving"]
    changed=deepcopy(after);changed["sample"][80*100+80]=[0,0,0]
    assert not same_pixels(selected,changed)
