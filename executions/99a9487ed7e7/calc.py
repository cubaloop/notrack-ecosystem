def average(nums):
    """
    Compute the average of a list of numbers.
    
    Args:
        nums: A non-empty list of numbers.
        
    Returns:
        The arithmetic mean of the numbers in the list.
        
    Raises:
        ValueError: If the list is empty.
    """
    if not nums:
        raise ValueError("Cannot compute average of an empty list")
    return sum(nums) / len(nums)


def clamp(val, low, high):
    """
    Clamp a value to be within the range [low, high].
    
    Args:
        val: The value to clamp.
        low: The lower bound.
        high: The upper bound.
        
    Returns:
        The clamped value: max(low, min(val, high)).
    """
    return max(low, min(val, high))


if __name__ == "__main__":
    # Simple self-test
    assert average([1, 2, 3, 4]) == 2.5
    assert average([10]) == 10.0
    assert average([1, 2, 3]) == 2.0
    try:
        average([])
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(15, 0, 10) == 10
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10
    assert clamp(5, 5, 5) == 5
    assert clamp(3, 1, 2) == 2
    assert clamp(0, 1, 2) == 1
