import base64
import json
import pandas as pd

def extract_payload(df, payload_col='payload_EncodedBase64', columns=False,
                    include_columns=None):
    """
    Extracts and decodes the Base64-encoded payload from the specified column in the DataFrame.

    By default, stores each decoded payload as a dictionary in a `payload`
    column. 
    Set `columns=True` to expand payload fields into separate columns.
    `include_columns` selects payload fields to retain; for expanded output,
    names may include flattened paths if dictionary values are nested.
    """
    # Decode Base64 and parse JSON into dictionaries
    payloads = df[payload_col].map(
        lambda x: json.loads(base64.b64decode(x)) if pd.notna(x) else {}
    )
    source_df = df.drop(columns=[payload_col])

    if columns:
        # Expand dictionary keys into columns
        payload_data = pd.json_normalize(payloads.tolist(), sep=".")
        payload_data.index = df.index
        if include_columns is not None:
            payload_data = payload_data.reindex(columns=include_columns)

        # Enrich the original DataFrame, preserving existing MQTT columns
        return pd.concat([source_df, payload_data], axis=1)

    # Keep selected payload fields together in a single dictionary column.
    if include_columns is not None:
        included = set(include_columns)
        payloads = payloads.map(
            lambda payload: {
                key: value for key, value in payload.items() if key in included
            }
        )
    payload_data = pd.DataFrame({'payload': payloads}, index=df.index)
    return pd.concat([source_df, payload_data], axis=1)

def convert_unix_time(df, column="TimeStamp_Unix", unit="s",
                      timezone="Europe/London", new_name=None):
    """Replace a Unix timestamp column with timezone-aware datetimes."""
    
    dt = pd.to_datetime(df[column], unit=unit, utc=True, errors="coerce")
    
    target_column = new_name or column
    df[target_column] = dt.dt.tz_convert(timezone) if timezone else dt
    if target_column != column:
        df = df.drop(columns=[column])
    
    return df

df = pd.read_csv("EMF_Camp\\Raw_data\\emf-mqtt-dump\\combined.csv\\mqtt.emf.camp.csv")
df.columns = ['topic', 'payload_EncodedBase64', 'MQTT Quality of Service (QoS)', 'Retained-message flag', 'TimeStamp_Unix', 'ElapsedTimeSincePrevious(s)']


weather_hq = df[df['topic'] == 'weather/hq']
weather_hq_decoded = extract_payload(weather_hq, 'payload_EncodedBase64')
weather_hq_decoded = convert_unix_time(weather_hq_decoded, "TimeStamp_Unix", new_name="Time")

print(weather_hq_decoded.head(10))  # Display the first 10 rows of the enriched DataFrame
print(weather_hq_decoded["payload"].iloc[0].keys())  # Display all payload keys from the first row

print(f"Feels like: {weather_hq_decoded['payload'].iloc[0].get('feelslike')} Runtime: {weather_hq_decoded['payload'].iloc[0].get('runtime')/60/60:.2f} Time: {weather_hq_decoded['Time'].iloc[0]}")  # Display the 'feelslike' value from the payload of the first row

topics = df['topic'].unique()

print(topics)







#### Quick vibecoded exploration of the data's topics 
# One row per unique topic
topic_catalog = (
    df["topic"]
    .value_counts()
    .rename_axis("topic")
    .reset_index(name="message_count")
)

# Split topics into hierarchical components
parts = topic_catalog["topic"].str.split("/")

# Record hierarchy depth
topic_catalog["depth"] = parts.str.len()

# Generate as many level columns as necessary
max_depth = int(topic_catalog["depth"].max())

levels = pd.DataFrame(
    parts.tolist(),
    columns=[f"level_{i}" for i in range(1, max_depth + 1)],
    index=topic_catalog.index,
)

topic_catalog = pd.concat([topic_catalog, levels], axis=1)

print(topic_catalog)

print(topic_catalog[(topic_catalog["level_1"] == "weather")])
print(topic_catalog[(topic_catalog["level_1"] == "bar")])
bar_topics = topic_catalog[(topic_catalog["level_1"] == "bar")]
bar_topics.to_csv("bar_topics.csv", index=False)

top_500_most_frequent_topics = topic_catalog.nlargest(500, "message_count")
top_500_most_frequent_topics.to_csv("top_500_most_frequent_topics.csv", index=False)