export class ObjList<T> {
  count: number;
  offset: number;
  objs: T[];
}

export class ObjListWithDates<T> extends ObjList<T> {
  start_date: number;
  end_date: number;
}
