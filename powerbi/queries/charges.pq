let
    Source = Csv.Document(File.Contents(DataFolder & "/charges.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"provider", type text}, {"tracking_id", type text}, {"ship_date", type date}, {"category", type text}, {"currency", type text}, {"amount_minor", Int64.Type}, {"fx_rate", type number}, {"amount_cny_minor", Int64.Type}, {"weight_kg", type number}, {"item_count", Int64.Type}, {"source_file", type text}, {"source_row", Int64.Type}, {"is_anomaly", Int64.Type}, {"amount", type number}, {"amount_cny", type number}}, "en-US"),
    Keyed = Table.AddColumn(Typed, "parcel_key", each Text.Combine({[provider], [tracking_id], Date.ToText([ship_date], "yyyy-MM-dd")}, "|"), type text)
in
    Keyed
