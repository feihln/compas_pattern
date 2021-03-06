__all__ = [
    'list_split',
    'are_items_in_list',
    'sublist_from_to_items_in_closed_list'
]


def list_split(l, indices):
    """Split list at given indices.
    Closed lists have the same first and last elements.
    If the list is closed, splitting wraps around if the first or last index is not in the indices to split.


    Parameters
    ----------
    l : list
            A list.
    indices : list
            A list of indices to split.

    Returns
    -------
    split_lists : list
            Nest lists from splitting the list at the given indices.

    """

    n = len(l)

    if l[0] == l[-1]:
        closed = True
        if n - 1 in indices:
            indices.remove(n - 1)
            if 0 not in indices:
                indices.append(0)
    else:
        closed = False

    indices = list(sorted(set(indices)))

    split_lists = []
    current_list = []
    for index, item in enumerate(l):
        current_list.append(item)
        if (index in indices and index != 0) or index == n - 1:
            split_lists.append(current_list)
            current_list = [item]

    if closed:
        if 0 not in indices:
            start = split_lists.pop(0)[1:]
            split_lists[-1] += start

    return split_lists


def sublist_from_to_items_in_closed_list(l, from_item, to_item):
    if from_item == to_item:
        return [from_item]
    if l[0] != l[-1]:
        l.append(l[0])
    from_idx = l.index(from_item)
    to_idx = l.index(to_item)
    sublists = list_split(l, [from_idx, to_idx])

    for sublist in sublists:
        if sublist[0] == from_item:
            return sublist


def are_items_in_list(items, l):
    """Check if items are in a list.

    Parameters
    ----------
    items : list
            A list of items (order does not matter).
    l : list
            A list.

    Returns
    -------
    bool
            True if all items are in the list. False otherwise.

    """

    for i in items:
        if i not in l:
            return False
    return True


def common_items(l1, l2):
    """Return common items in two lists.

    Parameters
    ----------
    l1 : list
            A list.
    l2 : list
            A list.

    Returns
    -------
    list
            The common items.

    """

    return [item for item in l1 if item in l2]


# ==============================================================================
# Main
# ==============================================================================

if __name__ == '__main__':

    import compas

    print list_split(range(20) + [0], [0, 8, 9, 12, 13])

    print sublist_from_to_items_in_closed_list(range(20), 13, 13)
