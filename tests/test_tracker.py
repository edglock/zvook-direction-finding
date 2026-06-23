from zvook_doa.tracker import DirectionTracker


def test_tracker_handles_azimuth_wraparound():
    tracker = DirectionTracker(min_update_confidence=0.1, smoothing=0.8)
    tracker.update(359.0, 10.0, 0.9, 0.0)
    result = tracker.update(1.0, 10.0, 0.9, 0.1)
    az = float(result["azimuth_deg"])
    assert az > 350.0 or az < 10.0
    assert result["status"] == "tracked"


def test_tracker_holds_on_low_confidence():
    tracker = DirectionTracker(min_update_confidence=0.5)
    tracker.update(45.0, 20.0, 0.9, 0.0)
    result = tracker.update(120.0, 20.0, 0.1, 0.1)
    assert result["status"] == "hold"
