from touchpoint import config, sounds


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


_MAIN_LIBRARY = {"progress": {"song": "prog.wav", "length": 7}}
_SPECIAL_LIBRARY = {"ariel": {"song": "ariel.wav", "length": 45}}


def test_choose_sound_uses_normal_library_when_no_special_card_configured(monkeypatch):
    monkeypatch.setattr(config, "SPECIAL_CARD_ID", "")
    name, sound, is_special = sounds.choose_sound("12345", _MAIN_LIBRARY, _SPECIAL_LIBRARY)
    assert name == "progress"
    assert is_special is False


def test_choose_sound_uses_special_library_when_card_matches(monkeypatch):
    monkeypatch.setattr(config, "SPECIAL_CARD_ID", "999888777")
    name, sound, is_special = sounds.choose_sound("999888777", _MAIN_LIBRARY, _SPECIAL_LIBRARY)
    assert name == "ariel"
    assert is_special is True


def test_choose_sound_uses_normal_library_when_card_does_not_match(monkeypatch):
    monkeypatch.setattr(config, "SPECIAL_CARD_ID", "999888777")
    name, sound, is_special = sounds.choose_sound("11111", _MAIN_LIBRARY, _SPECIAL_LIBRARY)
    assert name == "progress"
    assert is_special is False


def test_choose_sound_falls_back_when_special_library_is_empty(monkeypatch):
    # Card matches, but nothing's been added to the special collection yet
    # -- should degrade to normal behavior instead of crashing.
    monkeypatch.setattr(config, "SPECIAL_CARD_ID", "999888777")
    name, sound, is_special = sounds.choose_sound("999888777", _MAIN_LIBRARY, {})
    assert name == "progress"
    assert is_special is False
