from AutoWin.models.gemini import GeminiModel  # Import the Gemini model class

class ModelFactory:
    @staticmethod
    def create_model(model_name, *args): 
        if model_name.startswith('gemini'):  # Adjust the condition as per your Gemini model naming convention
            return GeminiModel(model_name, *args)
        else:
            raise ValueError(f'Unsupported model type {model_name}. Create entry in app/models/')
