let
    Source = Csv.Document(File.Contents(DataFolder & "/rejected.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"source_file", type text}, {"source_row", Int64.Type}, {"reason", type text}}, "en-US")
in
    Typed
