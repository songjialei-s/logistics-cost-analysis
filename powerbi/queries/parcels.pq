let
    Source = Csv.Document(File.Contents(DataFolder & "/parcels.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"provider", type text}, {"tracking_id", type text}, {"ship_date", type date}, {"item_count", Int64.Type}, {"weight_kg", type number}}, "en-US"),
    Keyed = Table.AddColumn(Typed, "parcel_key", each Text.Combine({[provider], [tracking_id], Date.ToText([ship_date], "yyyy-MM-dd")}, "|"), type text)
in
    Keyed
