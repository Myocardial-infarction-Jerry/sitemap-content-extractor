import os
from ollama import embed
from sklearn.metrics.pairwise import cosine_similarity


def read_md_files(directory):
    """Function to read all .md files from the 'texts/' directory"""
    file_contents = {}
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                file_contents[filename] = file.read()
    return file_contents


def embed_texts_and_keywords(files, keywords):
    """Function to embed a list of texts (i.e., content of .md files) and keywords"""
    # Embed the keywords
    keyword_embeddings = [embed(
        model='nomic-embed-text', input=keyword)['embeddings'] for keyword in keywords]
    keyword_embeddings = [embedding[0]
                          for embedding in keyword_embeddings]  # Flatten the embedding to 2D

    # Embed all the .md files
    file_embeddings = {}
    for filename, content in files.items():
        file_embedding = embed(model='nomic-embed-text',
                               input=content)['embeddings']
        # Flatten the embedding to 2D
        file_embeddings[filename] = file_embedding[0]

    return keyword_embeddings, file_embeddings


def sort_files_by_relevance(files, keyword_embeddings):
    """Function to sort the files based on their relevance to the keywords"""
    # Embed files and keywords
    keyword_embeddings, file_embeddings = embed_texts_and_keywords(
        files, keyword_embeddings)

    # Calculate similarity between keywords and each file's embedding
    similarity_scores = {}
    for filename, file_embedding in file_embeddings.items():
        file_relevance = 0
        # Calculate relevance for each keyword and sum the similarities
        for keyword_embedding in keyword_embeddings:
            similarity = cosine_similarity([keyword_embedding], [file_embedding])[
                0][0]  # Flatten result
            file_relevance += similarity

        # Store total relevance score for the file
        similarity_scores[filename] = file_relevance

    # Sort files by their total relevance score in descending order (higher relevance comes first)
    sorted_files = sorted(similarity_scores.items(),
                          key=lambda item: item[1], reverse=True)

    return sorted_files


if __name__ == '__main__':
    # Path to the 'texts/' directory
    directory = 'texts/'

    # Read all .md files
    files = read_md_files(directory)

    # Hardcoded keywords (you can adjust or add more keywords as needed)
    keywords = ['fall detect']

    # Sort the files by relevance to the keywords
    sorted_files = sort_files_by_relevance(files, keywords)

    # Print sorted files with relevance scores
    print("\nFiles sorted by relevance to the keywords:")
    for filename, relevance in sorted_files:
        print(f"{filename}: {relevance}")
