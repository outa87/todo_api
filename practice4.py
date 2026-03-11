def count_numbers(numbers):
    counts = {}
    
    for num in numbers:

        if num in counts:
            counts[num] += 1

        else:
            counts[num] = 1

    return counts

def get_max_number(counts):
    max_count = 0
    max_nums = []

    for num in counts:
        
        if counts[num] > max_count:

            max_count = counts[num]
            max_nums = [num]
        
        elif counts[num] == max_count:
            max_nums.append(num)

    return max_nums

numbers = [1, 2, 2, 2, 3, 3, 3,]

counts = count_numbers(numbers)
result = get_max_number(counts)

print(result)