import { Url } from './url';

export class FilteredPath {
  path: string;
  matching: boolean;
};

export class UrlAccess {
  id: number;
  url: Url;
  date: number;
  referer: Url;
  status: number;

  paths: FilteredPath[];
}

export const URL_HEIGHT = 50;
