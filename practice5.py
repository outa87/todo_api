def count_numbers(numbers):
    counts = {}

    for num in numbers:

        if num in counts:
            counts[num] += 1

        else:
            counts[num] = 1

    return counts

numbers = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5]
counts = count_numbers(numbers)
big1 = (None, -float("inf"))
big2 = (None, -float("inf"))
big3 = (None, -float("inf"))
for num in counts:
    
    if counts[num] > big1[1]:
        big3 = big2
        big2 = big1
        big1 = (num, counts[num])
    
    elif counts[num] > big2[1]:
        big3 = big2
        big2 = (num, counts[num])

    elif counts[num] > big3[1]:
        big3 = (num, counts[num])


