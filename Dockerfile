
FROM continuumio/miniconda3:latest

# Set the working directory
WORKDIR /app

# Copy the environment file
COPY environment.yml .

# Create the environment
RUN conda env create -f environment.yml

# Install MKL from conda-forge (replace intel channel)
RUN conda install -c conda-forge mkl=2023.1.0 -y

# Activate environment and set PATH
RUN echo "source activate kaleidoscope" > ~/.bashrc
ENV PATH /opt/conda/envs/kaleidoscope/bin:$PATH

# Copy project files
COPY . .

# Expose the application port
EXPOSE 5000

# Command to run the application
CMD ["python", "main.py"]
