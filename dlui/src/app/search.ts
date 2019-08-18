import { Url } from './url';
import { SearchEngine } from './search-engine';

export class Search {
    id: number;
    date: number;
    date_str?: string;
    query: string;
    search_engine: SearchEngine;
    results: Url[];
}
