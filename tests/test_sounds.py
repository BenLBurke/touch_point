from touchpoint import sounds


def test_default_effect_for_unknown_sound():
    plan = sounds.effect_for("does_not_exist", length=6)
    assert plan == {"type": "fade", "color": sounds.GREEN, "duration": 6}


def test_haunted_fades_purple():
    plan = sounds.effect_for("haunted", length=5)
    assert plan == {"type": "fade", "color": sounds.PURPLE, "duration": 5}


def test_pirates_and_saddle_both_fade_red():
    for name in ("pirates", "saddle"):
        plan = sounds.effect_for(name, length=4)
        assert plan["type"] == "fade"
        assert plan["color"] == sounds.RED


def test_mickey_and_tiki_share_double_fade():
    for name in ("mickey", "tiki"):
        plan = sounds.effect_for(name, length=999)
        assert plan["type"] == "double_fade"
        assert plan["colors"] == [sounds.RED, sounds.YELLOW]
        assert plan["duration"] == 2


def test_stop_us_is_chaos_with_fixed_duration():
    plan = sounds.effect_for("stop_us", length=7)
    assert plan == {"type": "chaos", "duration": 9}


def test_happily_is_fireworks():
    assert sounds.effect_for("happily", length=7) == {"type": "fireworks"}


def test_find_clip_looks_up_by_name():
    clip = sounds.find_clip("pirates")
    assert clip is not None
    assert clip.filename == "pirates.wav"
    assert clip.length == 4


def test_find_clip_returns_none_for_unknown_name():
    assert sounds.find_clip("nope") is None


def test_sound_library_names_are_unique():
    names = [clip.name for clip in sounds.SOUND_LIBRARY]
    assert len(names) == len(set(names))


def test_every_clip_has_an_effect_plan():
    # Every real sound in the library should resolve to a valid, known
    # effect type -- catches typos if a new sound is added without
    # wiring up (or deliberately falling back to the default for) it.
    valid_types = {"fade", "double_fade", "fireworks", "chaos"}
    for clip in sounds.SOUND_LIBRARY:
        plan = sounds.effect_for(clip.name, clip.length)
        assert plan["type"] in valid_types
