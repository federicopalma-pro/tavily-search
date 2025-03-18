import json
import os
import re
import traceback
from tavily import TavilyClient
from cat.mad_hatter.decorators import tool


@tool(
    return_direct=True,
    examples=[
        "search the web for contemporary art exhibitions in major European museums",
        "cerca sul web mostre d'arte contemporanea nei principali musei europei",
        "explore scientific sources online for information about Mediterranean diet benefits",
        "esplora fonti scientifiche online per informazioni sui benefici della dieta mediterranea",
        "find the latest research on effective teaching methods in primary education",
        "trova le ricerche più recenti sui metodi di insegnamento efficaci nella scuola primaria",
        "search advanced web results about Renaissance literature from domain:jstor.org",
        "cerca risultati web avanzati sulla letteratura rinascimentale dal domain:jstor.org",
        "limit the search to five travel guides for sustainable tourism in Southeast Asia",
        "limita la ricerca a cinque guide di viaggio per turismo sostenibile nel Sud-est asiatico",
        "narrow down to ten articles on Olympic Games history via tavily",
        "restringi i risultati a dieci articoli sulla storia dei Giochi Olimpici tramite tavily",
        "research advanced information on marine biodiversity from academic domains",
        "ricerca informazioni avanzate sulla biodiversità marina da domini accademici",
        "find the latest mental health research from domains:apa.org,who.int",
        "trova le più recenti ricerche sulla salute mentale dai domains:apa.org,who.int",
        "restrict results to three traditional recipes from around the world",
        "circoscrivi i risultati a tre ricette tradizionali da tutto il mondo",
        "find classical music composers from domain:music.edu",
        "trova compositori di musica classica dal domain:music.edu",
        "search for information about ancient Egyptian architecture from domain:archaeology.org",
        "cerca informazioni sull'architettura dell'antico Egitto dal domain:archaeology.org",
        "filter and show only seven parenting tips from domain:pediatrics.org",
        "filtra e mostra solo sette consigli per genitori dal domain:pediatrics.org",
        "research current trends in sustainable fashion from fashion magazines",
        "ricerca tendenze attuali nella moda sostenibile dalle riviste di moda",
        "return a maximum of eight natural remedies for common ailments",
        "riporta un massimo di otto rimedi naturali per disturbi comuni",
        "find recent discoveries in astronomy from domains:nasa.gov,esa.int",
        "trova le recenti scoperte in astronomia dai domains:nasa.gov,esa.int",
        "show me no more than six beginner-friendly gardening tips",
        "mostrami non più di sei consigli di giardinaggio per principianti",
        "discover critically acclaimed films of the last decade on the web",
        "scopri i film più acclamati dalla critica dell'ultimo decennio sul web",
        "research historical information about the Industrial Revolution from academic sources",
        "ricerca informazioni storiche sulla Rivoluzione Industriale da fonti accademiche",
        "gather only four economic forecasts for small businesses from domains:economist.com,bloomberg.com",
        "raccogli solo quattro previsioni economiche per piccole imprese dai domains:economist.com,bloomberg.com",
        "confine the search to a few effective workout routines from trustworthy fitness sources",
        "limita i risultati ad alcune routine di allenamento efficaci da fonti affidabili sul fitness",
        "I need three articles from repubblica.it about sport",
        "mi servono tre articoli su repubblica.it di sport",
        "search for news about climate change from the last 5 days",
        "cerca notizie sui cambiamenti climatici degli ultimi 5 giorni",
        "find news articles about financial markets from the past week",
        "trova articoli di notizie sui mercati finanziari dell'ultima settimana",
        "look for information on electric vehicles published in the last year",
        "cerca informazioni sui veicoli elettrici pubblicate nell'ultimo anno",
        "get the latest news from the last 2 days about technology startups",
        "ottieni le ultime notizie degli ultimi 2 giorni sulle startup tecnologiche",
        "search news from the past month about space exploration",
        "cerca notizie dell'ultimo mese sull'esplorazione spaziale",
        "find scientific research from the past year about quantum computing",
        "trova ricerche scientifiche dell'ultimo anno sul quantum computing",
        "get the most recent news about international politics from this week",
        "ottieni le notizie più recenti sulla politica internazionale di questa settimana",
        "search for the latest developments in AI from today",
        "cerca gli ultimi sviluppi nell'IA di oggi",
        "find all articles about Jannik Sinner on ubitennis.com from the last month and report a maximum of 10"
        "trovami tutti gli articoli che parlano di Jannik Sinner su ubitennis.com, nell’ultimo mese e riportane massimo 10",
    ],
)
def tavily_search(tool_input, cat):
    """
    Use this tool when the users ask to access the web, internet or online to seek information for answering their query.
    Utilizza questo strumento quando l'utente richiede di accedere al web, a internet o a risorse online per ottenere informazioni necessarie a rispondere alla sua domanda.
    Input is the query itself, including parameters: web domains and/or number of results desired, topic and time range.
    L'input è la query stessa, includi i parametri: i domini web e/o il numero di risultati richiesti, topic e intervallo di tempo.
    """

    # Get settings from the plugin
    settings = cat.mad_hatter.get_plugin().load_settings()
    api_key = settings.get("tavily_api_key", os.environ.get("TAVILY_API_KEY"))
    default_max_results = settings.get("max_results")
    default_search_depth = settings.get("search_depth")
    include_images = settings.get("include_images", False)
    include_answer = settings.get("include_answer", False)

    # Use the LLM to extract parameters
    extraction_prompt = f"""
    Extract search parameters from this query: "{tool_input}"
    
    Return must be a JSON object with these keys:
    - "include_domains": List of specific websites to search, like ["arxiv.org"]
    - "max_results": A number between 1 and {default_max_results}, based on the number of results requested by the user.
    - "topic": The category of the search, either "general","news" or "finance"
    - "time_range": The time range for results, either "day", "week", "month", "year" or "d", "w", "m", "y"
    
    For any parameter not specified in the query, use these defaults:
    - include_domains: [] (empty list)
    - max_results: {default_max_results}
    - topic: "general"
    - time_range: None

    Important note
    - "time_range" must be "day", "week", "month", "year" or "d", "w", "m", "y", please translated from other languages if necessary.
    """

    try:
        # Get the LLM to extract parameters
        llm_response = cat.llm(extraction_prompt)

        # Default parameters to use if parsing fails
        default_params = {
            "include_domains": [],
            "max_results": default_max_results,
            "topic": "general",
            "time_range": None,
        }

        # Parse the JSON response
        try:
            # Try to parse the JSON directly
            params = json.loads(llm_response)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from the text
            json_match = re.search(r"\{.*\}", llm_response, re.DOTALL)
            if json_match:
                try:
                    params = json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    # Fallback to defaults if JSON extraction fails
                    params = default_params
            else:
                # Fallback to defaults if no JSON pattern is found
                params = default_params

        # Extract and validate parameters
        include_domains = params.get("include_domains", [])
        if not isinstance(include_domains, list):
            include_domains = [include_domains] if include_domains else []

        max_results = params.get("max_results", default_max_results)
        try:
            max_results = int(max_results)
            # Ensure max_results doesn't exceed the setting value
            max_results = min(max_results, default_max_results)
        except (ValueError, TypeError):
            max_results = default_max_results

        topic = params.get("topic", "general")
        if topic not in ["general", "news", "finance"]:
            topic = "general"

        time_range = params.get("time_range")
        valid_time_ranges = ["day", "week", "month", "year", "d", "w", "m", "y"]
        if time_range and time_range not in valid_time_ranges:
            time_range = None

        # Initialize Tavily client
        client = TavilyClient(api_key=api_key)

        try:
            # Make the search request
            response = client.search(
                query=tool_input,
                search_depth=default_search_depth,
                include_answer=include_answer,
                max_results=max_results,
                include_domains=include_domains if include_domains else None,
                include_images=include_images,
                topic=topic,
                time_range=time_range,
            )

            # Format the results in a readable way instead of returning raw dictionary
            formatted_results = ""

            if not response.get("results") or not isinstance(response, dict):
                return "no results found"

            # Check if an answer is provided
            if include_answer and "answer" in response and response["answer"]:
                formatted_results += f"<p>{response['answer']}</p>"

            # Display search results first
            for i, result in enumerate(response["results"], 1):
                title = result.get("title", "No title")
                content = result.get("content", "No content available")
                url = result.get("url", "#")

                formatted_results += f"<h3>{i}. {title}</h3>"
                formatted_results += (
                    f"<p>{content[:300]}...</p>"
                    if len(content) > 300
                    else f"<p>{content}</p>"
                )
                # Use HTML formatting for clickable URL that opens in a new tab
                formatted_results += f'<p><a href="{url}" target="_blank">{url}</a></p>'

                # Add images if available and enabled
                if (
                    include_images
                    and "images" in result
                    and isinstance(result["images"], list)
                    and result["images"]
                ):
                    formatted_results += "<div class='images'>"
                    for img in result["images"]:
                        # Handle both string URLs and dictionary format
                        if isinstance(img, dict):
                            img_url = img.get("url", "")
                        elif isinstance(img, str):
                            img_url = img
                        else:
                            continue

                        if not img_url:
                            continue

                        # Add image with proper HTML syntax
                        formatted_results += f'<img src="{img_url}" alt="Image" />'

                    formatted_results += "</div>"

            # Add top-level images after all results
            if (
                include_images
                and "images" in response
                and isinstance(response["images"], list)
                and response["images"]
            ):
                formatted_results += "<div class='images'>"
                for img in response["images"]:
                    # Handle both string URLs and dictionary format
                    if isinstance(img, dict):
                        img_url = img.get("url", "")
                    elif isinstance(img, str):
                        img_url = img
                    else:
                        continue

                    if not img_url:
                        continue

                    # Add image with proper HTML syntax
                    formatted_results += f'<img src="{img_url}" alt="Image" />'

                formatted_results += "</div>"

            return formatted_results

        except Exception as e:
            # Provide more detailed error information
            error_details = traceback.format_exc()
            print(f"Error performing Tavily search: {str(e)}\nDetails: {error_details}")
            return "no results found"

    except Exception as e:
        print(f"Error processing Tavily search request: {str(e)}")
        return "no results found"
