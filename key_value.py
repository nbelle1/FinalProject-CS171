"""key_value.py"""

class KeyValue:
    """A key-value store used to manage contexts, queries, and responses."""

    def __init__(self):
        """
        Nik
        Initializes the KeyValue storage with an empty dictionary.
        Each context and its associated queries are stored in a nested structure.
        """
        self.data = {}

    def create_context(self, context_id):
        """
        Nik
        Creates a new context with a unique identifier.
        Args:
            context_id (str): A unique identifier for the context.
        """
        if context_id in self.data:
            print(f"DEBUG: Key-Value: Context with ID '{context_id}' already exists.")
        else:
            self.data[context_id] = {"queries": [], "responses": {}}
            # print(f"DEBUG: Key-Value: Context '{context_id}' created successfully.")

    def create_query(self, context_id, query_string):
        """
        Nik
        Adds a query to an existing context.
        Args:
            context_id (str): The identifier of the context.
            query_string (str): The query to add within the context.
        """
        if context_id not in self.data:
            print(f"Context '{context_id}' does not exist. Please create it first.")
            return

        self.data[context_id]["queries"].append(query_string)
        # print(f"DEBUG: Key-Value: Query added to context '{context_id}': {query_string}")

    def save_answer(self, context_id, response):
        """
        Nik
        Saves a selected answer to a specific query in a context.
        Args:
            context_id (str): The identifier of the context.
            response (str): Response to save.
        """
        if context_id not in self.data:
            print(f"Context '{context_id}' does not exist.")
            return

        queries = self.data[context_id]["queries"]
        if not queries:
            print(f"No queries exist in context '{context_id}' to associate the response with.")
            return

        # Associate the response with the latest query
        latest_query = queries[-1]
        self.data[context_id]["responses"][latest_query] = response
        print(f"Key Value: Response saved for the latest query '{latest_query}': {response}")

    def view(self, context_id):
        """
        Nik
        Retrieves information for a specified context.
        Args:
            context_id (str): The identifier of the context.
        Returns:
            dict: The context data if it exists, otherwise None.
        """
        if context_id not in self.data:
            return None

        context_data = self.data[context_id]
        queries = context_data["queries"]
        responses = context_data["responses"]

        # Build a formatted string for the queries and answers
        formatted_output = []
        for query in queries:
            answer = responses.get(query, "No answer provided")
            formatted_output.append(f"Query: {query}\nAnswer: {answer}")

        return "\n".join(formatted_output)
    
    

    def view_all(self):
        """
        Nik
        Retrieves all contexts and their associated data.
        Returns:
            dict: A dictionary where each key is a context ID and the value is a list of query-answer pairs.
        """
        if not self.data:
            return {}

        # Build structured data for all contexts
        result = {}
        for context_id, context_data in self.data.items():
            queries = context_data["queries"]
            responses = context_data["responses"]
            result[context_id] = [
                {"query": query, "answer": responses.get(query, "No answer provided")}
                for query in queries
            ]
        return result

