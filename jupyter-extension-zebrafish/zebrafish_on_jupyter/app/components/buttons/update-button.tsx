import * as React from "react";
import * as Immutable from "immutable";
import { connect } from "react-redux";
import { actions, selectors } from "@nteract/core";
import {
  AppState,
  ContentRef,
} from "@nteract/types";
import { CellId } from "@nteract/commutable";
import {
  Button,
} from 'semantic-ui-react'
import 'semantic-ui-css/semantic.min.css'

type ButtonProps = ButtonStateProps & ButtonOwnProps;

interface ButtonOwnProps {
  cellToUpdate: number;
  content: string;
  updateSource: function;
  fluid: bool;
}

interface ButtonStateProps {
  id: CellId;
  contentRef: ContentRef;
}

class UpdButton extends React.Component<ButtonProps> {
  onClick = () => {
    this.props.dispatch(
      actions.updateCellSource(
        {
          id: this.props.id,
          value: this.props.updateSource(),
          contentRef: this.props.contentRef
        }
      )
    );
    this.props.dispatch(actions.executeCell({id:this.props.id, contentRef:this.props.contentRef}));
  };

  render() {
    return (
      <Button
        onClick={this.onClick}
        content={this.props.content}
        fluid={this.props.fluid}
      >
      </Button>
    );
  }
}

const makeMapStateToProps = (
  initialState: AppState,
  { contentRef }: { contentRef: ContentRef }
) => {
  if (!contentRef) {
    throw new Error("<Notebook /> has to have a contentRef");
  }

  const mapStateToProps = (state: AppState, ownProps: ButtonOwnProps): ButtonStateProps => {
    const content = selectors.content(state, { contentRef });
    const model = selectors.model(state, { contentRef });

    if (!model || !content) {
      throw new Error(
        "<Notebook /> has to have content & model that are notebook types"
      );
    }

    if (model.type !== "notebook") {
      return {
        id: null,
        contentRef
      };
    }

    const id = model.notebook.cellOrder.get(ownProps.cellToUpdate)

    return {
      id,
      contentRef
    };
  };

  return mapStateToProps;
};

export const UpdateButton = connect(makeMapStateToProps)(UpdButton);
