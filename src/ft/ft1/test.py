from googlesearch import search


def google_search(query):
    try:
        # Perform the search and get the results as a generator
        search_results = search(query, num_results=1)

        # Convert the generator to a list and get the first result
        search_results_list = list(search_results)

        # Return the first result if available
        if search_results_list:
            return search_results_list[0]
        else:
            return "No results found"
    except Exception as e:
        return f"An error occurred: {e}"


# Example usage
query = "Social information processing"
first_result = google_search(query)
print(f"The first result is: {first_result}")
